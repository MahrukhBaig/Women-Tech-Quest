"""History table extractor module for reading historical consumption and payments."""

import json
import logging
from typing import List, Optional
from PIL import Image

from billdecoder.llm_client import GeminiClient
from billdecoder.models import HistoryExtraction, HistoryRow
from billdecoder.prompts import HISTORY_SYSTEM_PROMPT

logger = logging.getLogger("billdecoder.history")


def extract_history_table(
    client: GeminiClient,
    image: Image.Image,
    image_bytes: bytes,
    force_no_cache: bool = False,
) -> List[HistoryRow]:
    """Extract historical consumption rows from bill image.
    If table is absent, cut off, or unreadable, returns empty list [].
    NEVER invents or completes months.
    """
    try:
        resp_json = client.generate_structured(
            prompt=HISTORY_SYSTEM_PROMPT,
            image=image,
            image_bytes=image_bytes,
            response_schema=HistoryExtraction,
            force_no_cache=force_no_cache,
        )
        data = json.loads(resp_json)
        extraction = HistoryExtraction.model_validate(data)
        return extraction.rows
    except Exception as ex:
        logger.warning("History extraction failed or table absent: %s", ex)
        return []
