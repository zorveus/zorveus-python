import secrets
import hashlib
import base64

def generate_code_verifier(byte_length: int = 32) -> str:
    """Generates RFC 7636 code_verifier string."""
    verifier_bytes = secrets.token_bytes(byte_length)
    return base64.urlsafe_b64encode(verifier_bytes).decode("ascii").rstrip("=")

def generate_code_challenge(code_verifier: str) -> str:
    """Generates RFC 7636 S256 code_challenge string from verifier."""
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

def generate_state(byte_length: int = 32) -> str:
    """Generates random URL-safe state string for CSRF protection."""
    state_bytes = secrets.token_bytes(byte_length)
    return base64.urlsafe_b64encode(state_bytes).decode("ascii").rstrip("=")
