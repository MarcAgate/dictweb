from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.ui import STATIC_DIR
from app.routes.web import router as web_router

app = FastAPI(title="Dict Web", debug=True)

app.add_middleware(
    SessionMiddleware,
    secret_key="CHANGEZ-MOI-PLUS-TARD",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(web_router)

@app.get("/ping")
def ping():
    return {"status": "ok"}