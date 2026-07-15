"""Utilitarios de seguranca."""

import hashlib

def hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode()).hexdigest()
