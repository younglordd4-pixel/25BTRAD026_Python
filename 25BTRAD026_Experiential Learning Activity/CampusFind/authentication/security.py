"""
CampusFind - Security utilities
Password hashing, validation helpers, and token generation.
"""
import hashlib
import os
import secrets
import re
import string


def generate_salt() -> str:
    """Return a random 32-character hex salt."""
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """PBKDF2-HMAC-SHA256 with 310 000 iterations. Returns hex digest."""
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        310000
    ).hex()


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """Return True when *password* matches *stored_hash*."""
    return hash_password(password, salt) == stored_hash


def validate_email(email: str) -> bool:
    """Return True when *email* looks like a valid e-mail address."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple:
    """
    Validate password strength.

    Returns (True, 'Password is valid') on success, or
    (False, '<reason>') on failure.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"


def validate_usn(usn: str) -> bool:
    """Return True when *usn* is at least 5 alphanumeric characters."""
    return bool(usn and len(usn) >= 5 and usn.isalnum())


def generate_reset_token() -> str:
    """Return a URL-safe 32-byte random token for password resets."""
    return secrets.token_urlsafe(32)
