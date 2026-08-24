# Finpluse Biometric Security

We use the W3C WebAuthn / FIDO2 standard to support biometric authentication (FaceID, TouchID, Windows Hello) via Passkeys.

## Flow
1. **Registration**: Generate challenge -> User scans face/finger -> Verify and store public key credential.
2. **Authentication**: Generate challenge -> User authenticates -> Verify signed assertion -> Issue session token.

This ensures credentials never leave the device, providing phishing-resistant MFA.
