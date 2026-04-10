from passlib.context import CryptContext

from app.db import get_connection

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_user_by_username(username: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, password_hash, display_name, is_active
            FROM users
            WHERE username = ?
        """, (username,))
        return cur.fetchone()
    finally:
        conn.close()


def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)

    if user is None:
        return None

    if not user["is_active"]:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return user