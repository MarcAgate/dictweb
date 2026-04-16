from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.routes.web import router as web_router


app = FastAPI(title="Dict Web", debug=True)
app.add_middleware(
    SessionMiddleware,
    secret_key="CHANGEZ-MOI-PLUS-TARD",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(web_router)


@app.get("/ping")
def ping():
    return {"status": "ok"}