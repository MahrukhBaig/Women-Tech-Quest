"""Standard ASGI entrypoint for Vercel and ASGI runners."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api import app

__all__ = ["app"]

