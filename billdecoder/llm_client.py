"""Gemini LLM Client wrapper with rate limiting, retries, disk caching, and token logging."""

import hashlib
import json
import logging
import random
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union
from PIL import Image

from google import genai
from pydantic import BaseModel

from billdecoder.config import settings, PROMPT_VERSION

logger = logging.getLogger("billdecoder.llm")


class TokenUsageTracker:
    """Thread-safe tracker for cumulative token consumption."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.prompt_tokens: int = 0
        self.candidate_tokens: int = 0
        self.total_tokens: int = 0
        self.call_count: int = 0
        self.cached_hits: int = 0

    def record_call(self, prompt: int, candidates: int, total: int) -> None:
        with self.lock:
            self.prompt_tokens += prompt
            self.candidate_tokens += candidates
            self.total_tokens += total
            self.call_count += 1

    def record_cache_hit(self) -> None:
        with self.lock:
            self.cached_hits += 1

    def summary(self) -> Dict[str, int]:
        with self.lock:
            return {
                "calls": self.call_count,
                "cached_hits": self.cached_hits,
                "prompt_tokens": self.prompt_tokens,
                "candidate_tokens": self.candidate_tokens,
                "total_tokens": self.total_tokens,
            }


class RateLimiter:
    """Sliding-window rate limiter ensuring <= max_rpm calls per minute."""

    def __init__(self, max_rpm: int) -> None:
        self.max_rpm = max_rpm
        self.timestamps: List[float] = []
        self.lock = threading.Lock()

    def acquire(self) -> None:
        with self.lock:
            now = time.time()
            # Retain only timestamps from the last 60 seconds
            self.timestamps = [t for t in self.timestamps if now - t < 60.0]
            if len(self.timestamps) >= self.max_rpm:
                sleep_time = 60.0 - (now - self.timestamps[0]) + 0.1
                if sleep_time > 0:
                    logger.info("Rate limit throttle: sleeping %.2fs (limit=%d rpm)", sleep_time, self.max_rpm)
                    time.sleep(sleep_time)
            self.timestamps.append(time.time())


class GeminiClient:
    """Robust Gemini client tailored for competition constraints."""

    def __init__(self) -> None:
        settings.validate_or_raise()
        self.client = genai.Client(api_key=settings.api_key)
        self.model_name = settings.model_name
        self.rate_limiter = RateLimiter(settings.rate_limit_rpm)
        self.semaphore = threading.Semaphore(settings.max_concurrency)
        self.cache_dir = settings.cache_dir
        self.cache_enabled = settings.cache_enabled
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.usage = TokenUsageTracker()

    def _compute_cache_key(
        self, prompt: str, image_bytes: Optional[bytes] = None, schema_name: str = ""
    ) -> str:
        hasher = hashlib.sha256()
        hasher.update(self.model_name.encode("utf-8"))
        hasher.update(PROMPT_VERSION.encode("utf-8"))
        hasher.update(prompt.encode("utf-8"))
        hasher.update(schema_name.encode("utf-8"))
        if image_bytes:
            hasher.update(image_bytes)
        return hasher.hexdigest()

    def generate_structured(
        self,
        prompt: str,
        image: Optional[Image.Image] = None,
        image_bytes: Optional[bytes] = None,
        response_schema: Optional[Type[BaseModel]] = None,
        max_retries: int = 4,
        force_no_cache: bool = False,
    ) -> str:
        """Call Gemini with structured output, retries, backoff, and caching.
        Returns the raw JSON response text.
        """
        schema_name = response_schema.__name__ if response_schema else ""
        cache_key = self._compute_cache_key(prompt, image_bytes, schema_name)
        cache_file = self.cache_dir / f"{cache_key}.json"

        # Check disk cache
        if self.cache_enabled and not force_no_cache and cache_file.is_file():
            try:
                cached_text = cache_file.read_text(encoding="utf-8")
                self.usage.record_cache_hit()
                logger.info("Cache hit for key %s", cache_key[:12])
                return cached_text
            except Exception as e:
                logger.warning("Cache read failed: %s", e)

        # Prepare contents
        contents: List[Any] = [prompt]
        if image is not None:
            contents.append(image)

        config: Dict[str, Any] = {
            "temperature": 0.0,
        }
        if response_schema is not None:
            config["response_mime_type"] = "application/json"
            config["response_schema"] = response_schema

        last_exception: Optional[Exception] = None

        for attempt in range(max_retries):
            # Throttle and concurrency control
            self.rate_limiter.acquire()
            with self.semaphore:
                try:
                    logger.info(
                        "Calling %s (attempt %d/%d)",
                        self.model_name,
                        attempt + 1,
                        max_retries,
                    )
                    resp = self.client.models.generate_content(
                        model=self.model_name,
                        contents=contents,
                        config=config,
                    )

                    # Record token usage counts only
                    if hasattr(resp, "usage_metadata") and resp.usage_metadata:
                        p_tok = resp.usage_metadata.prompt_token_count or 0
                        c_tok = resp.usage_metadata.candidates_token_count or 0
                        t_tok = resp.usage_metadata.total_token_count or 0
                        self.usage.record_call(p_tok, c_tok, t_tok)
                        logger.info("Call token usage: prompt=%d, candidate=%d, total=%d", p_tok, c_tok, t_tok)

                    resp_text = resp.text.strip() if resp.text else "{}"

                    # Write to cache
                    if self.cache_enabled and not force_no_cache:
                        try:
                            cache_file.write_text(resp_text, encoding="utf-8")
                        except Exception as ce:
                            logger.warning("Cache write failed: %s", ce)

                    return resp_text

                except Exception as ex:
                    last_exception = ex
                    err_str = str(ex).lower()
                    # Check for rate limit or server errors
                    is_retryable = any(
                        term in err_str
                        for term in [
                            "429",
                            "quota",
                            "resource_exhausted",
                            "resourceexhausted",
                            "500",
                            "503",
                            "internal",
                            "unavailable",
                            "timeout",
                        ]
                    )
                    if is_retryable and attempt < max_retries - 1:
                        backoff = (2.0 ** attempt) * 2.0 + random.uniform(0.2, 1.2)
                        logger.warning(
                            "Retryable error encountered (%s). Backing off %.2fs...",
                            type(ex).__name__,
                            backoff,
                        )
                        time.sleep(backoff)
                    else:
                        logger.error("LLM call failed on attempt %d: %s", attempt + 1, type(ex).__name__)
                        if not is_retryable:
                            raise ex

        if last_exception:
            raise last_exception
        raise RuntimeError("LLM call failed after retries.")


# Global client instance
_client_instance: Optional[GeminiClient] = None


def get_llm_client() -> GeminiClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = GeminiClient()
    return _client_instance
