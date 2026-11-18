"""API-02 (token), EVT, CMP, COM, NTF, worker işleri ve güvenlik alarmları."""

from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.worker import jobs
from tests.conftest import API, OWNER, PASSWORD, Api, World, security_events


def _token(api: Api, scopes: list[str]) -> str:
    r = api.post("/me/api-tokens", json={"name": "mcp", "scopes": scopes})
    assert r.status_code == 201, r.text
    assert r.json()["token"].startswith("cth_")
    return r.json()["token"]


def test_api_token_scope_and_role_intersection(world: World, login) -> None:  # type: ignore[no-untyped-def]
    raw = _token(login("analyst.soc1"), ["tasks:read"])
    bot = Api(TestClient(app), token=raw)
    assert bot.get("/tasks").status_code == 200
    assert bot.get(f"/tasks/{world.tasks['pentest_todo'].id}").status_code == 404  # rol kapsamı geçerli
    assert bot.post("/tasks", json={"type": "STANDARD", "title": "bot task"}).status_code == 403  # scope yok
    assert bot.get("/dashboard/summary").status_code == 403
    assert bot.get("/users").status_code == 403  # sadece web oturumu
    assert bot.get("/me/api-tokens").status_code == 403


def test_token_listing_hides_secret_and_revoke_works(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("analyst.soc1")
    raw = _token(api, ["tasks:read", "reports:read"])
    listed = api.get("/me/api-tokens").json()
    assert "token" not in listed[0] and raw.split("_")[1] == listed[0]["prefix"]
    api.delete(f"/me/api-tokens/{listed[0]['id']}")
    assert Api(TestClient(app), token=raw).get("/tasks").status_code == 401
    assert security_events("API_TOKEN_INVALID") == 1


def test_events_rules(world: World, login) -> None:  # type: ignore[no-untyped-def]
    emp = login("analyst.soc1")
    start = datetime.now(UTC) + timedelta(days=3)
    base = {
        "title": "BSides",
        "type": "CONFERENCE",
        "startsAt": start.isoformat(),
        "endsAt": (start + timedelta(hours=8)).isoformat(),
    }
    assert emp.post("/events", json={**base, "scope": "CORPORATE"}).status_code == 403
    assert (
        emp.post("/events", json={**base, "scope": "INDIVIDUAL", "url": "javascript:alert(1)"}).status_code
        == 400
    )
    r = emp.post("/events", json={**base, "scope": "INDIVIDUAL", "url": "https://bsides.example"})
    assert r.status_code == 201
    ev = r.json()["id"]
    p = emp.post(f"/events/{ev}/participations", json={"role": "ATTENDEE"})
    assert p.status_code == 201 and p.json()["status"] == "REQUESTED"
    assert emp.post(f"/events/{ev}/participations", json={"role": "ATTENDEE"}).status_code == 409
    other = str(world.users["analyst.soc2"].id)
    assert (
        emp.post(f"/events/{ev}/participations", json={"role": "ATTENDEE", "userId": other}).status_code
        == 403
    )
    pid = p.json()["id"]
    assert (
        login("manager.pentest").patch(f"/participations/{pid}", json={"status": "APPROVED"}).status_code
        == 404
    )
    r = login("manager.soc").patch(f"/participations/{pid}", json={"status": "APPROVED"})
    assert r.status_code == 200 and r.json()["decidedBy"]["fullName"]
    assert emp.patch(f"/participations/{pid}", json={"status": "REJECTED"}).status_code == 422
    types = [n["type"] for n in emp.get("/notifications").json()["items"]]
    assert "PARTICIPATION_DECIDED" in types
    assert emp.get("/events?participantId=me").json()["total"] == 1


def test_competencies(world: World, login) -> None:  # type: ignore[no-untyped-def]
    mgr = login("manager.soc")
    assert (
        login("analyst.soc1")
        .post("/competencies", json={"name": "SIEM", "category": "DEFENSIVE"})
        .status_code
        == 403
    )
    cid = mgr.post("/competencies", json={"name": "SIEM", "category": "DEFENSIVE"}).json()["id"]
    emp = login("analyst.soc1")
    me = str(world.users["analyst.soc1"].id)
    assert emp.put(f"/users/{me}/competencies/{cid}", json={"level": 6}).status_code == 400
    assert emp.put(f"/users/{me}/competencies/{cid}", json={"level": 4}).status_code == 200
    assert emp.put(f"/users/{me}/competencies/{cid}", json={"level": 4, "verified": True}).status_code == 403
    other = str(world.users["analyst.soc2"].id)
    assert emp.put(f"/users/{other}/competencies/{cid}", json={"level": 2}).status_code == 403
    r = mgr.put(f"/users/{me}/competencies/{cid}", json={"level": 4, "verified": True})
    assert r.status_code == 200 and r.json()["verifiedBy"] is not None
    matrix = mgr.get(f"/competencies/matrix?teamId={world.teams['soc'].id}").json()
    assert matrix["members"] and matrix["competencies"][0]["name"] == "SIEM"
    assert emp.get(f"/competencies/matrix?teamId={world.teams['soc'].id}").status_code == 403


def test_announcements(world: World, login) -> None:  # type: ignore[no-untyped-def]
    mgr = login("manager.soc")
    body = {"scope": "TEAM", "teamId": str(world.teams["soc"].id), "title": "Vardiya", "body": "Yeni plan"}
    assert mgr.post("/announcements", json=body).status_code == 201
    assert mgr.post("/announcements", json={**body, "scope": "ORGANIZATION"}).status_code == 403
    assert login("analyst.soc1").get("/announcements").json()["total"] == 1
    assert login("analyst.pentest1").get("/announcements").json()["total"] == 0
    assert login("analyst.soc1").get("/notifications/unread-count").json()["count"] == 1


def test_notifications_read_all(world: World, login) -> None:  # type: ignore[no-untyped-def]
    login("manager.soc").post(
        "/tasks",
        json={
            "type": "STANDARD",
            "title": "Bildirim",
            "teamId": str(world.teams["soc"].id),
            "assigneeId": str(world.users["analyst.soc1"].id),
        },
    )
    emp = login("analyst.soc1")
    assert emp.get("/notifications/unread-count").json()["count"] == 1
    assert emp.post("/notifications/read-all").status_code == 204
    assert emp.get("/notifications/unread-count").json()["count"] == 0


def test_recurring_generation_is_idempotent(world: World) -> None:
    day = date.today()
    while day.weekday() >= 5:  # DAILY = iş günleri
        day -= timedelta(days=1)
    with Session(OWNER) as db:
        first = jobs.generate_recurring_tasks(db, today=day)
        db.commit()
        second = jobs.generate_recurring_tasks(db, today=day)
        db.commit()
    assert first >= 1 and second == 0


def test_due_soon_notifications_deduplicated(world: World) -> None:
    with Session(OWNER) as db:
        first = jobs.due_soon_notifications(db)
        db.commit()
        again = jobs.due_soon_notifications(db)
        db.commit()
    assert first == 1 and again == 0


def test_brute_force_alert_on_security_summary(world: World, login, anon: TestClient) -> None:  # type: ignore[no-untyped-def]
    for _ in range(6):
        anon.post(
            f"{API}/auth/login", json={"email": "analyst.soc2@demo.local", "password": "bad" + PASSWORD}
        )
    s = login("director").get("/security/summary?window=1h").json()
    rules = {a["rule"] for a in s["openAlerts"]}
    assert {"brute_force", "account_lockout"} <= rules
    assert s["countsByType"]["LOGIN_FAILED"] >= 5
    assert s["topSources"][0]["count"] >= 5


def test_metrics_summary_for_director(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("director")
    api.get("/tasks")
    m = api.get("/system/metrics-summary?window=15m").json()
    assert any(e["route"] == "/api/v1/tasks" for e in m["endpoints"])
    assert {j["name"] for j in m["jobs"]} >= {"generate_recurring_tasks"}
