import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def make_new_key(salt: bytes, pwd: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=880000,
    )
    return base64.urlsafe_b64encode(kdf.derive(bytes(pwd, 'utf-8')))


def encrypt(f: Fernet, text: str) -> bytes:
    return f.encrypt(bytes(text, 'utf-8'))


def encrypt2(f: Fernet, text: str) -> bytes:
    return f.encrypt(bytes(text, 'utf-8'))


def decrypt(f: Fernet, data: bytes) -> str:
    return str(f.decrypt(data), 'utf-8')
