"""
Finpluse v2 -- Multi-Modal Input API
"""
from typing import Any
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from pydantic import BaseModel

from app.multimodal.nlp.expense_parser import NLExpenseParser
from app.multimodal.vision.receipt_parser import ReceiptParser

router = APIRouter()
nl_parser = NLExpenseParser()
receipt_parser = ReceiptParser()


class NLRequest(BaseModel):
    text: str


@router.post("/parse-text")
async def parse_natural_language(req: NLRequest) -> dict[str, Any]:
    """Parse natural language expense entry."""
    if not req.text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    parsed = nl_parser.parse(req.text)
    return {"parsed_expense": parsed}


@router.post("/upload-receipt")
async def upload_receipt(file: UploadFile = File(...)) -> dict[str, Any]:
    """Process a receipt image.
    
    In a real app, this would call Tesseract or Google Cloud Vision.
    Here we simulate the OCR output.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # SIMULATED OCR OUTPUT
    mock_ocr = """
    WHOLE FOODS MARKET
    123 Main St
    Austin, TX 78701
    10/24/2026
    
    Organic Bananas    $2.99
    Almond Milk        $4.50
    Avocado            $1.50
    
    SUBTOTAL           $8.99
    TAX                $0.74
    TOTAL             $9.73
    """
    
    parsed = receipt_parser.parse_ocr_text(mock_ocr)
    return {"parsed_receipt": parsed, "raw_ocr": mock_ocr}
