from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import CSRF_COOKIE, SESSION_COOKIE, Principal, SessionOnly, current_principal
from app.config import get_settings
from app.db import get_db
from app.modules.auth import service

router = APIRouter(tags=["Auth"])


def _set_cookies(response: Response, raw: str, csrf: str, max_age: int) -> None:
    secure = get_settings().cookie_secure
    response.set_cookie(
        SESSION_COOKIE, raw, max_age=max_age, httponly=True, secure=secure, samesite="lax", path="/"
    )
    response.set_cookie(
        CSRF_COOKIE, csrf, max_age=max_age, httponly=False, secure=secure, samesite="lax", path="/"
    )


@router.post("/auth/login", operation_id="login", response_model=c.Session, response_model_by_alias=True)
def login(
    body: c.LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)
) -> c.Session:
    raw, sess = service.login(db, str(body.email), body.password, request.cookies.get(SESSION_COOKIE))
    db.flush()
    _set_cookies(response, raw, sess.csrf_token, get_settings().session_hours * 3600)
    return service.session_payload(db, sess.user, sess.csrf_token, sess.expires_at)


@router.post("/auth/logout", operation_id="logout", status_code=204, dependencies=[SessionOnly])
def logout(
    response: Response, principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> Response:
    service.logout(db, principal)
    out = Response(status_code=204)
    out.delete_cookie(SESSION_COOKIE, path="/")
    out.delete_cookie(CSRF_COOKIE, path="/")
    return out


@router.get("/auth/me", operation_id="getMe", response_model=c.Session)
def me(principal: Principal = Depends(current_principal), db: Session = Depends(get_db)) -> c.Session:
    csrf = principal.session.csrf_token if principal.session else ""
    expires = principal.session.expires_at if principal.session else None
    return service.session_payload(db, principal.user, csrf, expires)
