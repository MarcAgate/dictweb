import os
import sys
import sqlite3
from pathlib import Path

if getattr(sys, "frozen", False):
    exe_dir = Path(sys.executable).resolve().parent
    bundle_dir = Path(getattr(sys, "_MEIPASS", exe_dir)).resolve()

    db_in_bundle = bundle_dir / "MsTibTool.db"
    db_next_to_exe = exe_dir / "MsTibTool.db"

    if db_in_bundle.exists() and db_in_bundle.stat().st_size > 0:
        DB_PATH = db_in_bundle
    elif db_next_to_exe.exists() and db_next_to_exe.stat().st_size > 0:
        DB_PATH = db_next_to_exe
    else:
        DB_PATH = db_in_bundle
else:
    project_dir = Path(__file__).resolve().parent.parent
    DB_PATH = project_dir / "MsTibTool.db"

print("========== DB DEBUG START ==========")
print("PID       =", os.getpid())
print("FROZEN    =", getattr(sys, "frozen", False))
print("EXECUTABLE=", sys.executable)
print("CWD       =", Path.cwd())
print("DB_PATH   =", DB_PATH)
print("ABS_PATH  =", DB_PATH.resolve())
print("EXISTS    =", DB_PATH.exists())
if DB_PATH.exists():
    print("SIZE      =", DB_PATH.stat().st_size, "bytes")
print("========== DB DEBUG END ============")

def get_connection():
    print("----- get_connection() -----")
    print("PID       =", os.getpid())
    print("DB_PATH   =", DB_PATH)
    print("ABS_PATH  =", DB_PATH.resolve())
    print("EXISTS    =", DB_PATH.exists())
    if DB_PATH.exists():
        print("SIZE      =", DB_PATH.stat().st_size, "bytes")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    rows = conn.execute("PRAGMA database_list").fetchall()
    print("PRAGMA database_list =", [tuple(r) for r in rows])

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    print("TABLES =", [r[0] for r in tables])
    print("----------------------------")
    return conn