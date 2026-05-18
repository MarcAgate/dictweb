import threading
import time
import webbrowser
import urllib.request
import uvicorn


URL = "http://127.0.0.1:8000/login"


def run_server():
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,
    )


def wait_for_server(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/login", timeout=1) as r:
                if 200 <= r.status < 500:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


if __name__ == "__main__":
    t = threading.Thread(target=run_server, daemon=False)
    t.start()

    if wait_for_server():
        webbrowser.open(URL)

    t.join()