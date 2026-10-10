"""Packaging and verification script for WTQ Build Track submission.
Builds the required ZIP structure, scans for secrets, checks size <= 15 MB, and verifies contents.
"""

import os
import re
import sys
import zipfile
from pathlib import Path
from typing import List, Set
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_DIR = PROJECT_ROOT / "output"
SUBMISSION_ZIP = PROJECT_ROOT / "wtq-submission.zip"
MAX_ZIP_BYTES = 15 * 1024 * 1024  # 15 MB

# Secret patterns
SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),  # Google API Key pattern
    re.compile(r"sk-[a-zA-Z0-9]{32,}"),   # OpenAI API Key pattern
    re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}"),  # Slack Token pattern
]


def get_actual_api_keys() -> List[str]:
    """Retrieve actual environment keys to ensure they NEVER appear in any packaged file."""
    keys = []
    for var in ("API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        val = os.getenv(var)
        if val and len(val.strip()) > 8:
            keys.append(val.strip())
    return keys


def scan_file_for_secrets(file_path: Path, actual_keys: List[str]) -> List[str]:
    """Scan a single file for accidental secret leaks."""
    issues = []
    # Skip binary files from regex scan
    if file_path.suffix.lower() in (".png", ".jpg", ".jpeg", ".mp4", ".mov", ".webm", ".pyc"):
        return issues

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return issues

    # 1. Check for actual key string
    for k in actual_keys:
        if k in content:
            issues.append(f"CRITICAL: Found actual live API key string in {file_path.name}!")

    # 2. Check for secret patterns (excluding .env.example which has placeholder)
    if file_path.name != ".env.example":
        for pat in SECRET_PATTERNS:
            if pat.search(content):
                issues.append(f"CRITICAL: Found potential API key pattern match in {file_path.name}!")

    return issues


def collect_source_files() -> List[Path]:
    """Collect project source files while strictly excluding secrets, caches, and venvs."""
    included: List[Path] = []
    excluded_names = {
        ".env", ".venv", "__pycache__", ".git", ".cache", "node_modules",
        "bill_cache", ".pytest_cache", "scratch_guide.txt", "guide_clean.txt",
        "bills", "dev_output", "train", "test", "demo_output"
    }

    # Core source files at root
    for fname in ["README.md", ".env.example", "requirements.txt", "api.py", "package_submission.py"]:
        p = PROJECT_ROOT / fname
        if p.is_file():
            included.append(p)

    # Directories to include under source/
    for folder in ["billdecoder", "tests", "static"]:
        fpath = PROJECT_ROOT / folder
        if fpath.is_dir():
            for p in fpath.rglob("*"):
                if p.is_file():
                    # Check exclusions in path parts
                    if any(part in excluded_names for part in p.parts):
                        continue
                    if p.suffix.lower() in (".pyc", ".tmp", ".log"):
                        continue
                    included.append(p)

    return included


def build_submission_zip() -> int:
    print("=" * 65)
    print("      WTQ BUILD TRACK SUBMISSION PACKAGER")
    print("=" * 65)

    actual_keys = get_actual_api_keys()
    print(f"Loaded {len(actual_keys)} active environment key(s) to verify zero leaks.")

    # 1. Verify output CSVs exist
    level1_csv = OUTPUT_DIR / "level1.csv"
    level2_csv = OUTPUT_DIR / "level2.csv"

    # If output files don't exist yet, check dev_output for dry-run
    if not level1_csv.is_file() or not level2_csv.is_file():
        dev_l1 = PROJECT_ROOT / "tests" / "dev_output" / "level1.csv"
        dev_l2 = PROJECT_ROOT / "tests" / "dev_output" / "level2.csv"
        if dev_l1.is_file() and dev_l2.is_file():
            print("\n[NOTE] Official output/level1.csv not found yet. Using tests/dev_output for packaging test.")
            level1_csv = dev_l1
            level2_csv = dev_l2
        else:
            print("\n[ERROR] Missing output/level1.csv and output/level2.csv.")
            print("Please run the CLI to generate results before packaging.")
            return 1

    # 2. Collect and scan source files
    source_files = collect_source_files()
    print(f"Collected {len(source_files)} source files to package.")

    all_issues = []
    for sf in source_files + [level1_csv, level2_csv]:
        issues = scan_file_for_secrets(sf, actual_keys)
        all_issues.extend(issues)

    if all_issues:
        print("\n[FAIL] SECRET SCAN DETECTED ISSUES:")
        for iss in all_issues:
            print(f"  {iss}")
        print("\nPackaging aborted to protect your API keys!")
        return 1
    else:
        print("[PASS] Secret scan clear: 0 live API keys or pattern leaks detected.")

    # 3. Create ZIP
    if SUBMISSION_ZIP.exists():
        SUBMISSION_ZIP.unlink()

    print(f"\nCreating {SUBMISSION_ZIP.name}...")
    with zipfile.ZipFile(SUBMISSION_ZIP, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Add output CSVs
        zf.write(level1_csv, arcname="output/level1.csv")
        zf.write(level2_csv, arcname="output/level2.csv")

        # Add source files
        for sf in source_files:
            rel = sf.relative_to(PROJECT_ROOT)
            zf.write(sf, arcname=f"source/{rel.as_posix()}")

        # Check for optional demo video
        demo_dir = PROJECT_ROOT / "demo"
        if demo_dir.is_dir():
            for v in demo_dir.glob("*"):
                if v.suffix.lower() in (".mp4", ".mov", ".webm"):
                    print(f"Adding demo video: {v.name}")
                    zf.write(v, arcname=f"demo/{v.name}")

    # 4. Check size
    zip_size_bytes = SUBMISSION_ZIP.stat().st_size
    zip_size_mb = zip_size_bytes / (1024 * 1024)
    print(f"\nFinal ZIP Size: {zip_size_bytes:,} bytes ({zip_size_mb:.2f} MB)")

    if zip_size_bytes > MAX_ZIP_BYTES:
        print(f"[FAIL] ZIP size exceeds the 15 MB limit! ({zip_size_mb:.2f} MB > 15.00 MB)")
        return 1

    # 5. Print contents inventory
    print("\n--- ZIP Contents Inventory ---")
    with zipfile.ZipFile(SUBMISSION_ZIP, mode="r") as zf:
        for info in zf.infolist():
            print(f"  {info.filename:<48} ({info.file_size:,} bytes)")

    print("\n" + "=" * 65)
    print(" [SUCCESS] Submission ZIP is valid, safe, and ready to submit!")
    print(f" File path: {SUBMISSION_ZIP}")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(build_submission_zip())
