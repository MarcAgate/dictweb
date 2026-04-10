from app.auth import hash_password
from app.db import get_connection

username = "admin"
password = "admin"
display_name = "Administrateur"

password_hash = hash_password(password)

conn = get_connection()
try:
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (username, password_hash, display_name, is_active)
        VALUES (?, ?, ?, 1)
    """, (username, password_hash, display_name))
    conn.commit()
    print("Utilisateur créé.")
finally:
    conn.close()