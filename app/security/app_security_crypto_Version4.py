from cryptography.fernet import Fernet, InvalidToken
from ..config import settings

_fernet = None

def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = settings.ENCRYPTION_KEY.encode()
        _fernet = Fernet(key)
    return _fernet

def encrypt_str(plaintext: str) -> str:
    f = _get_fernet()
    token = f.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")

def decrypt_str(ciphertext: str) -> str:
    f = _get_fernet()
    try:
        data = f.decrypt(ciphertext.encode("utf-8"))
        return data.decode("utf-8")
    except InvalidToken:
        raise ValueError("Invalid encryption token")