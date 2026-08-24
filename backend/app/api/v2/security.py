"""
Finpluse v2 -- Security & Biometrics API
"""
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.security.webauthn import WebAuthnManager

router = APIRouter()
webauthn = WebAuthnManager()


class RegOptionsRequest(BaseModel):
    user_id: str
    username: str

class VerificationRequest(BaseModel):
    user_id: str
    response: dict[str, Any]


@router.post("/webauthn/register/options")
async def register_options(req: RegOptionsRequest) -> dict[str, Any]:
    """Generate options for passkey registration."""
    return webauthn.generate_registration(req.user_id, req.username)


@router.post("/webauthn/register/verify")
async def register_verify(req: VerificationRequest) -> dict[str, bool]:
    """Verify and save new passkey."""
    success = webauthn.verify_registration(req.user_id, req.response)
    if not success:
        raise HTTPException(status_code=400, detail="Verification failed")
    return {"success": True}


@router.post("/webauthn/authenticate/options")
async def auth_options(user_id: str) -> dict[str, Any]:
    """Generate options for passkey authentication."""
    return webauthn.generate_authentication(user_id)


@router.post("/webauthn/authenticate/verify")
async def auth_verify(req: VerificationRequest) -> dict[str, bool]:
    """Verify passkey authentication assertion."""
    success = webauthn.verify_authentication(req.user_id, req.response)
    if not success:
        raise HTTPException(status_code=401, detail="Authentication failed")
    return {"success": True, "token": "mock_jwt_token_for_biometric_session"}
