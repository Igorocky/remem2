import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def random_salt(len: int = 32) -> str:
    return str(base64.urlsafe_b64encode(os.urandom(len)), 'utf-8')


def make_new_key(salt: str, pwd: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=base64.urlsafe_b64decode(bytes(salt, 'utf-8')),
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(bytes(pwd, 'utf-8')))


def encrypt(text: str, f: Fernet) -> bytes:
    return f.encrypt(bytes(text, 'utf-8'))


def decrypt(data: bytes, f: Fernet) -> str:
    return str(f.decrypt(data), 'utf-8')
