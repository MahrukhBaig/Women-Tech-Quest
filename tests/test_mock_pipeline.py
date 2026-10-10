"""Mock end-to-end pipeline test verifying the complete workflow without calling the real LLM."""

import io
import json
from unittest.mock import MagicMock
from PIL import Image

from billdecoder.models import HistoryExtraction, HistoryRow, Level1Bill, Level2AnswersResponse
from billdecoder.pipeline import PipelineTracker, process_bill


def create_dummy_png_bytes() -> bytes:
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_mock_pipeline():
    dummy_bytes = create_dummy_png_bytes()
    mock_client = MagicMock()

    # Level 1 mock response
    mock_l1 = {
        "provider": "KE",
        "tariff": "A1-R",
        "sanctioned_load_kw": 3,
        "bill_month": "2026-04",
        "reading_date": "2026-04-03",
        "issue_date": "2026-04-07",
        "due_date": "2026-04-21",
        "previous_reading": 8819,
        "current_reading": 8970,
        "units_consumed": 151,
        "charges": [{"type": "energy", "amount": 1054}],
        "total_charges": 1054,
        "taxes": [{"type": "gst", "amount": 200}],
        "total_taxes": 200,
        "current_bill": 1254,
        "arrears": 0,
        "payable_within_due_date": 1254,
        "payable_after_due_date": 1350,
    }

    # History mock response
    mock_history = HistoryExtraction(
        rows=[
            HistoryRow(month="2025-07", units=239, bill_amount=6000),
            HistoryRow(month="2025-08", units=180, bill_amount=4000),
        ]
    )

    # Level 2 mock response
    mock_l2 = Level2AnswersResponse(
        answers=[
            {
                "question_id": "Q1",
                "answer": "Taxes and duties total PKR 200 out of your current bill of PKR 1254, or about 15.95%.",
            }
        ]
    )

    # Configure side effects for sequential calls
    mock_client.generate_structured.side_effect = [
        json.dumps(mock_l1),
        mock_history.model_dump_json(),
        mock_l2.model_dump_json(),
    ]

    tracker = PipelineTracker()
    questions = [{"question_id": "Q1", "question": "How much of my bill is taxes?"}]

    res = process_bill(
        image_input=dummy_bytes,
        bill_id="KESC_0008",
        questions=questions,
        client=mock_client,
        tracker=tracker,
    )

    assert res["bill_id"] == "KESC_0008"
    assert res["level1_bill"].provider == "KE"
    assert res["answers"]["Q1"].startswith("Taxes and duties")
    assert len(tracker.fallbacks) == 0
