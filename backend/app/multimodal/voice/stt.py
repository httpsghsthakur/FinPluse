"""
Finpluse v2 -- Speech-to-Text (Voice Module)
"""
import logging
from typing import BinaryIO

logger = logging.getLogger(__name__)

def transcribe_audio(audio_file: BinaryIO) -> str:
    """
    Mock implementation of Whisper STT.
    In production, this would call OpenAI Whisper API or use a local model.
    """
    # Read a few bytes just to simulate processing
    audio_file.read(10)
    logger.info("Mock STT: Transcribing audio...")
    return "What is my current balance?"

