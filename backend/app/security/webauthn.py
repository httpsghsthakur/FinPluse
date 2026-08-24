"""
Finpluse v2 -- WebAuthn (Passkeys & Biometrics)

Handles registration and authentication using FIDO2 / WebAuthn standards.
Supports FaceID, TouchID, and Windows Hello.
"""
import base64
import json
import logging
import os
from typing import Any

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

logger = logging.getLogger(__name__)

# In-memory store for demo. In production, use DB.
_challenges: dict[str, str] = {}
_credentials: dict[str, list[dict[str, Any]]] = {}

RP_ID = os.environ.get("RP_ID", "localhost")
RP_NAME = "Finpluse Security"
ORIGIN = os.environ.get("ORIGIN", "http://localhost:5173")


class WebAuthnManager:
    """Manages FIDO2 WebAuthn flows."""

    def generate_registration(self, user_id: str, username: str) -> dict[str, Any]:
        """Generate options for registering a new passkey/biometric."""
        options = generate_registration_options(
            rp_id=RP_ID,
            rp_name=RP_NAME,
            user_id=user_id.encode(),
            user_name=username,
            authenticator_selection=AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment.PLATFORM, # Force FaceID/TouchID etc
                resident_key=ResidentKeyRequirement.REQUIRED,
                user_verification=UserVerificationRequirement.REQUIRED,
            ),
            attestation=AttestationConveyancePreference.NONE,
        )
        
        # Store challenge
        _challenges[user_id] = options.challenge.hex()
        
        return json.loads(options.json())

    def verify_registration(self, user_id: str, response: dict[str, Any]) -> bool:
        """Verify the credential from the authenticator and save it."""
        expected_challenge = _challenges.pop(user_id, None)
        if not expected_challenge:
            logger.warning(f"No challenge found for user {user_id}")
            return False

        try:
            verification = verify_registration_response(
                credential=response,
                expected_challenge=bytes.fromhex(expected_challenge),
                expected_rp_id=RP_ID,
                expected_origin=ORIGIN,
            )
            
            # Save credential
            if user_id not in _credentials:
                _credentials[user_id] = []
                
            _credentials[user_id].append({
                "credential_id": verification.credential_id.hex(),
                "public_key": verification.credential_public_key.hex(),
                "sign_count": verification.sign_count,
            })
            return True
            
        except Exception as e:
            logger.error(f"Registration verification failed: {e}")
            return False

    def generate_authentication(self, user_id: str) -> dict[str, Any]:
        """Generate options for authenticating with an existing passkey."""
        creds = _credentials.get(user_id, [])
        allow_credentials = [{"type": "public-key", "id": bytes.fromhex(c["credential_id"])} for c in creds]

        options = generate_authentication_options(
            rp_id=RP_ID,
            allow_credentials=allow_credentials,
            user_verification=UserVerificationRequirement.REQUIRED,
        )
        
        _challenges[user_id] = options.challenge.hex()
        return json.loads(options.json())

    def verify_authentication(self, user_id: str, response: dict[str, Any]) -> bool:
        """Verify the authentication assertion."""
        expected_challenge = _challenges.pop(user_id, None)
        if not expected_challenge:
            return False

        creds = _credentials.get(user_id, [])
        credential_id_hex = response.get("id", "")
        
        # Find matching credential
        matching_cred = next((c for c in creds if c["credential_id"] == credential_id_hex), None)
        if not matching_cred:
            return False

        try:
            verification = verify_authentication_response(
                credential=response,
                expected_challenge=bytes.fromhex(expected_challenge),
                expected_rp_id=RP_ID,
                expected_origin=ORIGIN,
                credential_public_key=bytes.fromhex(matching_cred["public_key"]),
                credential_current_sign_count=matching_cred["sign_count"],
                require_user_verification=True,
            )
            
            # Update sign count to prevent replay attacks
            matching_cred["sign_count"] = verification.new_sign_count
            return True
            
        except Exception as e:
            logger.error(f"Authentication verification failed: {e}")
            return False
