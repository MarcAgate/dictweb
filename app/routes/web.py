from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import authenticate_user
from app.search import prepare_search_view_data, fetch_sources_grouped

from typing import List
from app.search import prepare_search_view_data, fetch_sources_grouped

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

    sources_grouped = fetch_sources_grouped()

    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "q": "",
            "match_mode": "exact",
            "selected_key": "",
            "entries": [],
            "selected_entry": None,
            "result_count": 0,
            "sources_grouped": sources_grouped,
            "selected_sources": [],
        }
    )


from typing import List

@router.post("/search", response_class=HTMLResponse)
def search_submit(
    request: Request,
    q: str = Form(""),
    match_mode: str = Form("exact"),
    sources: List[str] = Form([]),
    selected_key: str = Form("")
):
    if not request.session.get("username"):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    sources_grouped = fetch_sources_grouped()

    view_data = prepare_search_view_data(
        term=q,
        match_mode=match_mode,
        sources=sources,
        lang="",
        contexte="",
        selected_key=selected_key
    )

    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "q": q,
            "match_mode": match_mode,
            "selected_key": view_data["selected_key"],
            "entries": view_data["entries"],
            "selected_entry": view_data["selected_entry"],
            "result_count": view_data["result_count"],
            "sources_grouped": sources_grouped,
            "selected_sources": sources,
        }
    )