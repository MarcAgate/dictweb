from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import authenticate_user
from app.search import prepare_search_view_data

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    username = request.session.get("username")

    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"username": username}
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": None}
    )


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if not authenticate_user(username, password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Identifiants invalides."}
        )

    request.session["username"] = username

    return RedirectResponse(
        url=request.url_for("search_page"),
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/search", response_class=HTMLResponse)
def search_page(request: Request):
    if not request.session.get("username"):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "q": "",
            "match_mode": "exact",
            "source": "",
            "lang": "",
            "contexte": "",
            "selected_key": "",
            "entries": [],
            "selected_entry": None,
            "result_count": 0
        }
    )


@router.post("/search", response_class=HTMLResponse)
def search_submit(
    request: Request,
    q: str = Form(""),
    match_mode: str = Form("exact"),
    source: str = Form(""),
    lang: str = Form(""),
    contexte: str = Form(""),
    selected_key: str = Form("")
):
    if not request.session.get("username"):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    view_data = prepare_search_view_data(
        term=q,
        match_mode=match_mode,
        source=source,
        lang=lang,
        contexte=contexte,
        selected_key=selected_key
    )

    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "q": q,
            "match_mode": match_mode,
            "source": source,
            "lang": lang,
            "contexte": contexte,
            "selected_key": selected_key,
            "entries": view_data["entries"],
            "selected_entry": view_data["selected_entry"],
            "result_count": view_data["result_count"]
        }
    )