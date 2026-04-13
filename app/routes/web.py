import hashlib
import hmac
import os
from typing import List
from urllib.parse import urlparse

from fastapi import APIRouter, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import authenticate_user
from app.search import fetch_sources_grouped, prepare_search_view_data

router = APIRouter()
templates = Jinja2Templates(directory="templates")

SEARCH_LINK_SECRET = os.getenv("DICTWEB_SEARCH_LINK_SECRET", "CHANGE-ME-SEARCH-LINK-SECRET")


def sign_search_term(term: str) -> str:
    payload = (term or "").strip().encode("utf-8")
    return hmac.new(
        SEARCH_LINK_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


def is_valid_search_signature(term: str, signature: str) -> bool:
    if not signature:
        return False

    expected = sign_search_term(term)
    return hmac.compare_digest(expected, signature)


def _same_origin(url_value: str, request: Request) -> bool:
    if not url_value:
        return False

    try:
        parsed = urlparse(url_value)
    except Exception:
        return False

    request_scheme = request.url.scheme
    request_netloc = request.url.netloc

    return parsed.scheme == request_scheme and parsed.netloc == request_netloc


def ensure_internal_get_request(request: Request, q: str, sig: str) -> None:
    if not q.strip():
        return

    if not is_valid_search_signature(q, sig):
        raise HTTPException(status_code=403, detail="Signature de lien invalide.")

    origin = (request.headers.get("origin") or "").strip()
    referer = (request.headers.get("referer") or "").strip()

    if origin:
        if not _same_origin(origin, request):
            raise HTTPException(status_code=403, detail="Origin non autorisée.")
        return

    if referer:
        if not _same_origin(referer, request):
            raise HTTPException(status_code=403, detail="Referer non autorisé.")
        return

    raise HTTPException(
        status_code=403,
        detail="Requête GET refusée : provenance interne non vérifiable.",
    )


@router.get("/", response_class=HTMLResponse, name="home")
def home(request: Request):
    username = request.session.get("username")

    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"username": username},
    )


@router.get("/login", response_class=HTMLResponse, name="login_page")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": None},
    )


@router.post("/login", response_class=HTMLResponse, name="login_submit")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if not authenticate_user(username, password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Identifiants invalides."},
        )

    request.session["username"] = username

    return RedirectResponse(
        url=request.url_for("search_page"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/logout", name="logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/search", response_class=HTMLResponse, name="search_page")
def search_page(
    request: Request,
    q: str = Query(""),
    match_mode: str = Query("exact"),
    selected_key: str = Query(""),
    sig: str = Query(""),
):
    if not request.session.get("username"):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    sources_grouped = fetch_sources_grouped()

    if q.strip():
        ensure_internal_get_request(request, q, sig)

        view_data = prepare_search_view_data(
            term=q,
            match_mode=match_mode,
            sources=[],
            lang="",
            contexte="",
            selected_key=selected_key,
        )

        selected_entry = view_data["selected_entry"]
        selected_entry_tabs = selected_entry["tabs"] if selected_entry else {"fr": [], "eng": [], "tib": []}

        return templates.TemplateResponse(
            request=request,
            name="search.html",
            context={
                "q": q,
                "matchmode": match_mode,
                "selectedkey": view_data["selected_key"],
                "entries": view_data["entries"],
                "selectedentry": selected_entry,
                "selectedentrytabs": selected_entry_tabs,
                "resultcount": view_data["result_count"],
                "sourcesgrouped": sources_grouped,
                "selectedsources": [],
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "q": "",
            "matchmode": "exact",
            "selectedkey": "",
            "entries": [],
            "selectedentry": None,
            "selectedentrytabs": {"fr": [], "eng": [], "tib": []},
            "resultcount": 0,
            "sourcesgrouped": sources_grouped,
            "selectedsources": [],
        },
    )


@router.post("/search", response_class=HTMLResponse, name="search_submit")
def search_submit(
    request: Request,
    q: str = Form(""),
    match_mode: str = Form("exact"),
    sources: List[str] = Form([]),
    selected_key: str = Form(""),
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
        selected_key=selected_key,
    )

    selected_entry = view_data["selected_entry"]
    selected_entry_tabs = selected_entry["tabs"] if selected_entry else {"fr": [], "eng": [], "tib": []}

    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "q": q,
            "matchmode": match_mode,
            "selectedkey": view_data["selected_key"],
            "entries": view_data["entries"],
            "selectedentry": selected_entry,
            "selectedentrytabs": selected_entry_tabs,
            "resultcount": view_data["result_count"],
            "sourcesgrouped": sources_grouped,
            "selectedsources": sources,
        },
    )