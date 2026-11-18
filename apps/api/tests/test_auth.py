"""AUT-01, AUT-03, T01–T03, T12, T14: kimlik doğrulama, kilitleme, CSRF, oturum."""

from fastapi.testclient import TestClient

from tests.conftest import API, PASSWORD, World, security_events


def _login(client: TestClient, email: str, password: str = PASSWORD):  # type: ignore[no-untyped-def]
    return client.post(f"{API}/auth/login", json={"email": email, "password": password})


def test_login_success_sets_httponly_session_and_returns_scope(world: World, anon: TestClient) -> None:
    r = _login(anon, "manager.soc@demo.local")
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["role"] == "MANAGER"
    assert len(body["visibleTeamIds"]) == 2 and len(body["managedTeamIds"]) == 2
    cookie = r.headers.get_list("set-cookie")
    session_cookie = next(c for c in cookie if c.startswith("cth_session="))
    assert "HttpOnly" in session_cookie and "SameSite=lax" in session_cookie
    assert security_events("LOGIN_SUCCESS") == 1


def test_visible_teams_per_role(world: World, login) -> None:  # type: ignore[no-untyped-def]
    assert len(login("analyst.soc1").get("/auth/me").json()["visibleTeamIds"]) == 1
    assert len(login("director").get("/auth/me").json()["visibleTeamIds"]) == 3
    assert len(login("auditor").get("/auth/me").json()["managedTeamIds"]) == 0


def test_wrong_password_and_unknown_user_return_same_generic_error(world: World, anon: TestClient) -> None:
    a = _login(anon, "analyst.soc1@demo.local", "wrong-password")
    b = _login(anon, "nobody@demo.local", "wrong-password")
    assert a.status_code == b.status_code == 401
    assert a.json()["detail"] == b.json()["detail"]


def test_account_locks_after_five_failures_even_with_correct_password(world: World, anon: TestClient) -> None:
    for _ in range(5):
        assert _login(anon, "analyst.soc1@demo.local", "wrong-password").status_code == 401
    r = _login(anon, "analyst.soc1@demo.local")
    assert r.status_code == 423
    assert security_events("ACCOUNT_LOCKED") == 1


def test_logout_invalidates_session(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("analyst.soc1")
    assert api.post("/auth/logout").status_code == 204
    api.c.cookies.clear()
    assert api.get("/auth/me").status_code == 401


def test_old_cookie_rejected_after_logout(world: World, anon: TestClient) -> None:
    r = _login(anon, "analyst.soc1@demo.local")
    raw = r.cookies["cth_session"]
    anon.post(f"{API}/auth/logout", headers={"X-CSRF-Token": r.json()["csrfToken"]})
    fresh = TestClient(anon.app)
    fresh.cookies.set("cth_session", raw)
    assert fresh.get(f"{API}/auth/me").status_code == 401


def test_csrf_required_for_cookie_writes(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("manager.soc")
    r = api.post(
        "/tasks",
        json={"type": "STANDARD", "title": "CSRF testi", "teamId": str(world.teams["soc"].id)},
        headers={"X-CSRF-Token": "wrong"},
    )
    assert r.status_code == 403
    assert security_events("CSRF_REJECTED") == 1


def test_unauthenticated_access_rejected(world: World, anon: TestClient) -> None:
    for path in ("/tasks", "/dashboard/summary", "/users", "/security/events", "/audit-logs"):
        assert anon.get(API + path).status_code == 401, path


def test_inactive_user_cannot_login(world: World, login, anon: TestClient) -> None:  # type: ignore[no-untyped-def]
    director = login("director")
    uid = str(world.users["analyst.soc3"].id)
    assert director.patch(f"/users/{uid}", json={"isActive": False}).status_code == 200
    assert _login(anon, "analyst.soc3@demo.local").status_code == 401


def test_errors_are_problem_json_without_internals(world: World, anon: TestClient) -> None:
    r = anon.post(f"{API}/auth/login", json={"email": "not-an-email", "password": "x", "extra": 1})
    assert r.status_code == 400
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert {"type", "title", "status", "requestId"} <= body.keys()
    assert "Traceback" not in r.text and "not-an-email" not in r.text


def test_security_headers_present(world: World, anon: TestClient) -> None:
    r = anon.get(f"{API}/health")
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]


def test_payload_too_large(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("manager.soc")
    r = api.post("/tasks", content=b"x" * 300_000, headers={"content-type": "application/json"})
    assert r.status_code == 413
    assert security_events("PAYLOAD_TOO_LARGE") == 1
