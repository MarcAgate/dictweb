import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "MsTibTool.db"

print("========== DB DEBUG START ==========")
print("PID       =", os.getpid())
print("BASE_DIR  =", BASE_DIR)
print("DB_PATH   =", DB_PATH)
print("ABS_PATH  =", DB_PATH.resolve())
print("EXISTS    =", DB_PATH.exists())
print("IS_FILE   =", DB_PATH.is_file())
print("CWD       =", Path.cwd())

if DB_PATH.exists():
    try:
        print("SIZE      =", DB_PATH.stat().st_size, "bytes")
    except Exception as e:
        print("SIZE_ERR  =", repr(e))
else:
    print("SIZE      = <missing file>")

print("========== DB DEBUG END ============")


def get_connection():
    print("----- get_connection() -----")
    print("PID       =", os.getpid())
    print("DB_PATH   =", DB_PATH)
    print("ABS_PATH  =", DB_PATH.resolve())
    print("EXISTS    =", DB_PATH.exists())

    if DB_PATH.exists():
        try:
            print("SIZE      =", DB_PATH.stat().st_size, "bytes")
        except Exception as e:
            print("SIZE_ERR  =", repr(e))
    else:
        print("SIZE      = <missing file>")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        row = conn.execute("PRAGMA database_list").fetchall()
        print("PRAGMA database_list =", [tuple(r) for r in row])
    except Exception as e:
        print("PRAGMA_ERR =", repr(e))

    print("----------------------------")
    return conn