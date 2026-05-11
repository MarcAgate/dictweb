import threading
import webbrowser
import uvicorn

from app.main import app

def open_browser():
    webbrowser.open("http://127.0.0.1:8000/login")

if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)