from flask_bcrypt import generate_password_hash, check_password_hash

def hash_password(plain: str) -> str:
    return generate_password_hash(plain).decode('utf-8')

def verify_password(hashed: str, plain: str) -> bool:
    return check_password_hash(hashed, plain)
