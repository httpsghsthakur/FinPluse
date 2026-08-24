import pytest
from app.multimodal.vision.receipt_parser import ReceiptParser

def test_parse_receipt():
    # Mock bytes
    res = ReceiptParser().parse_ocr_text("mock image data")
    assert "merchant" in res
    assert "total_amount" in res


