"""Parola hash'leme (argon2id)."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_ph = PasswordHasher()  # argon2id, kütüphane varsayılan parametreleri
# Var olmayan kullanıcı için de doğrulama yapılır (zamanlama ile kullanıcı numaralandırmayı önler, T12).
_DUMMY_HASH = _ph.hash("not-a-real-password-for-timing-only")


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _ph.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
