import time
import bcrypt
import jwt
import config
from db import pool

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())

def create_access_token(user_id: int, email: str) -> str:
    payload = {"sub": str(user_id), "email": email, "exp": int(time.time()) + config.JWT_EXPIRY_HOURS * 3600}
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])

def create_user(email: str, password: str) -> int:
    password_hash = hash_password(password)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO app_user (email, password_hash) VALUES (%s, %s) RETURNING user_id",
                (email, password_hash),
            )
            return cur.fetchone()["user_id"]

def authenticate_user(email: str, password: str) -> dict | None:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, email, password_hash FROM app_user WHERE email = %s",
                (email,),
            )
            row = cur.fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        return None
    return {"user_id": row["user_id"], "email": row["email"]}