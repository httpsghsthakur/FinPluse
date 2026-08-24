"""
Finpluse v2 -- Multimodal Input API
"""
from typing import Any
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException

from app.api.deps import get_current_user
from app.db.models.user import User
from app.multimodal.voice.stt import transcribe_audio
from app.multimodal.voice.nlu import extract_intent_and_entities
from app.multimodal.voice.response import generate_response
from app.multimodal.vision.receipt_parser import ReceiptParser
from app.multimodal.nlp.expense_parser import NLExpenseParser

router = APIRouter()

@router.post("/voice")
async def process_voice(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Process voice input."""
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")
        
    text = transcribe_audio(audio.file)
    nlu_res = extract_intent_and_entities(text)
    
    # Mock data fetch based on intent
    mock_data = {"balance": 15420.50, "amount": 120.00, "anomaly_count": 0, "runway_days": 45}
    response_text = generate_response(nlu_res["intent"], nlu_res["entities"], mock_data)
    
    return {
        "transcription": text,
        "intent": nlu_res["intent"],
        "entities": nlu_res["entities"],
        "response": response_text
    }

@router.post("/receipt")
async def upload_receipt(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Process a receipt image."""
    if not image.filename:
        raise HTTPException(status_code=400, detail="No image provided")
        
    img_bytes = await image.read()
    receipt_data = ReceiptParser().parse_ocr_text(img_bytes.decode('utf-8', errors='ignore'))
    return receipt_data

@router.post("/expense")
async def log_expense_nl(
    text: str = Form(...),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Log an expense using natural language."""
    parsed = NLExpenseParser().parse(text)
    if not parsed:
        raise HTTPException(status_code=400, detail="Could not parse expense from text")
        
    # In a real app, we would save this to the database here
    return {
        "status": "success",
        "parsed_transaction": parsed
    }



