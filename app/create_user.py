from app.auth import hash_password
from app.db import get_connection

username = "anila"
password = "clairesicard2026"
display_name = "Anila"
role = "viewer"

password_hash = hash_password(password)

conn = get_connection()
try:
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (username, password_hash, display_name, is_active, role)
        VALUES (?, ?, ?, 1,?)
    """, (username, password_hash, display_name,role))
    conn.commit()
    print("Utilisateur créé.")
finally:
    conn.close()