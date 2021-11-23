import hashlib


def hash_password(password: str) -> str:
    h = hashlib.sha256()
    h.update(password.encode())
    return h.hexdigest()
