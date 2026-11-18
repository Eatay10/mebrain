"""TASK-019: organizasyon hiyerarşisi (unit), görünürlük, atama kuralları, ilerleme/timeline, takip (yıldız),
çalışma arkadaşları, ekler, yetkinlik puanı/öneri, planlı raporlar ve proje organizasyon ağacı."""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.contract import CompetencyCategory, EventScope, EventType, ParticipationRole, ParticipationStatus
from app.models import Competency, Event, EventParticipation, UserCompetency
from tests.conftest import OWNER, World, audit_actions

ac = pytest.mark.ac


def _uid(w: World, key: str) -> str:
    return str(w.users[key].id)


def _tid(w: World, key: str) -> str:
    return str(w.tasks[key].id)


def _titles(api, **params) -> set[str]:  # type: ignore[no-untyped-def]
    r = api.get("/tasks", params={"pageSize": 100, **params})
    assert r.status_code == 200, r.text
    return {t["title"] for t in r.json()["items"]}


# ------------------------------------------------------------------ görünürlük
@ac("TASK-019/AC-1")
def test_visibility_by_hierarchy(world: World, login) -> None:  # type: ignore[no-untyped-def]
    assert _titles(login("unit.defense")) == {
        "soc_todo",
        "soc_overdue",
        "soc_done",
        "soc_project",
        "vuln_todo",
    }
    assert "pentest_todo" in _titles(login("director")) and "pentest_todo" in _titles(login("auditor"))
    emp = _titles(login("analyst.soc1"))
    assert "soc_todo" in emp and "pentest_todo" not in emp and "vuln_todo" not in emp
    assert login("analyst.soc1").get(f"/tasks/{_tid(world, 'pentest_todo')}").status_code == 404


@ac("TASK-019/AC-1")
def test_involved_user_sees_task_outside_own_team(world: World, login) -> None:  # type: ignore[no-untyped-def]
    pm = login("manager.pentest")
    r = pm.post(
        "/tasks",
        json={
            "type": "STANDARD",
            "title": "Ortak çalışma",
            "teamId": str(world.teams["pentest"].id),
            "assigneeId": _uid(world, "analyst.pentest1"),
        },
    )
    assert r.status_code == 201
    # Pentest yöneticisi SOC çalışanını ekleyemez (kapsamı dışında)
    assert (
        pm.patch(
            f"/tasks/{r.json()['id']}",
            json={"version": 1, "collaboratorIds": [_uid(world, "analyst.soc1")]},
        ).status_code
        == 400
    )
    # Direktör ekleyebilir; SOC çalışanı artık bu task'ı görür
    d = login("director")
    upd = d.patch(
        f"/tasks/{r.json()['id']}", json={"version": 1, "collaboratorIds": [_uid(world, "analyst.soc1")]}
    )
    assert upd.status_code == 200, upd.text
    assert [c["fullName"] for c in upd.json()["collaborators"]] == ["Analyst Soc1"]
    assert "Ortak çalışma" in _titles(login("analyst.soc1"))
    assert "Ortak çalışma" in _titles(login("analyst.soc1"), assigneeId="me")


# ------------------------------------------------------------------ atama kuralları
@ac("TASK-019/AC-2")
def test_assignment_chain_director_unit_manager_manager(world: World, login) -> None:  # type: ignore[no-untyped-def]
    soc = str(world.teams["soc"].id)
    d = login("director")
    r = d.post(
        "/tasks",
        json={
            "type": "STANDARD",
            "title": "Unit hedefleri",
            "teamId": soc,
            "assigneeId": _uid(world, "unit.defense"),
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["requester"]["fullName"] == "Director"

    um = login("unit.defense")
    names = {u["fullName"] for u in um.get("/me/assignable-users").json()}
    assert {"Manager Soc", "Analyst Soc1", "Analyst Vuln1"} <= names and "Analyst Pentest1" not in names
    ok = um.post(
        "/tasks",
        json={
            "type": "STANDARD",
            "title": "Kapasite planı",
            "teamId": soc,
            "assigneeId": _uid(world, "manager.soc"),
        },
    )
    assert ok.status_code == 201, ok.text
    bad = um.post(
        "/tasks",
        json={
            "type": "STANDARD",
            "title": "Kapsam dışı",
            "teamId": soc,
            "assigneeId": _uid(world, "analyst.pentest1"),
        },
    )
    assert bad.status_code == 400
    # Unit yöneticisi kendi unit'i dışındaki ekipte task açamaz
    assert (
        um.post(
            "/tasks", json={"type": "STANDARD", "title": "x yz", "teamId": str(world.teams["pentest"].id)}
        ).status_code
        == 404
    )

    mgr = names_for(login("manager.soc"))
    assert "Analyst Vuln1" in mgr and "Manager Pentest" not in mgr and "Unit Defense" not in mgr


def names_for(api) -> set[str]:  # type: ignore[no-untyped-def]
    return {u["fullName"] for u in api.get("/me/assignable-users").json()}


@ac("TASK-019/AC-2")
def test_requester_backup_and_collaborators(world: World, login) -> None:  # type: ignore[no-untyped-def]
    mgr = login("manager.soc")
    r = mgr.post(
        "/tasks",
        json={
            "type": "STANDARD",
            "title": "Çok kişili",
            "teamId": str(world.teams["soc"].id),
            "assigneeId": _uid(world, "analyst.soc1"),
            "backupAssigneeId": _uid(world, "analyst.soc2"),
            "collaboratorIds": [_uid(world, "analyst.soc3")],
            "requesterId": _uid(world, "unit.defense"),
        },
    )
    assert r.status_code == 201, r.text
    t = r.json()
    assert t["requester"]["fullName"] == "Unit Defense"
    assert t["backupAssignee"]["fullName"] == "Analyst Soc2"
    assert [c["fullName"] for c in t["collaborators"]] == ["Analyst Soc3"]
    # Yedek sorumlu otomatik takipçi
    assert [u["fullName"] for u in mgr.get(f"/tasks/{t['id']}/watchers").json()] == ["Analyst Soc2"]
    types = [n["type"] for n in login("analyst.soc3").get("/notifications").json()["items"]]
    assert "TASK_ASSIGNED" in types
    dup = mgr.post(
        "/tasks",
        json={
            "type": "STANDARD",
            "title": "Çakışan kişi",
            "teamId": str(world.teams["soc"].id),
            "assigneeId": _uid(world, "analyst.soc1"),
            "collaboratorIds": [_uid(world, "analyst.soc1")],
        },
    )
    assert dup.status_code == 400


# ------------------------------------------------------------------ ilerleme + timeline + takipçi bildirimi
@ac("TASK-019/AC-3")
def test_progress_timeline_and_watcher_notification(world: World, login) -> None:  # type: ignore[no-untyped-def]
    tid = _tid(world, "soc_todo")
    watcher = login("analyst.soc3")
    assert watcher.put(f"/tasks/{tid}/watch").status_code == 204
    assert watcher.get(f"/tasks/{tid}").json()["isWatching"] is True
    assert _titles(watcher, watching="true") == {"soc_todo"}

    emp = login("analyst.soc1")
    r = emp.post(f"/tasks/{tid}/progress", json={"progress": 25, "note": "Kapsam netleşti", "version": 1})
    assert r.status_code == 200, r.text
    assert r.json()["progress"] == 25 and r.json()["status"] == "IN_PROGRESS"
    r = emp.post(
        f"/tasks/{tid}/progress", json={"progress": 70, "note": "Test ortamı doğrulandı", "version": 2}
    )
    assert r.status_code == 200
    assert (
        emp.post(f"/tasks/{tid}/progress", json={"progress": 80, "note": "eski", "version": 2}).status_code
        == 409
    )

    timeline = emp.get(f"/tasks/{tid}/progress").json()
    assert [(e["fromProgress"], e["toProgress"], e["note"]) for e in timeline] == [
        (0, 25, "Kapsam netleşti"),
        (25, 70, "Test ortamı doğrulandı"),
    ]
    titles = [
        n["title"] for n in watcher.get("/notifications").json()["items"] if n["type"] == "TASK_PROGRESS"
    ]
    assert "Analyst Soc1 ilerlemeyi %70 yaptı: Test ortamı doğrulandı" in titles
    # Yedek sorumlu (soc2) otomatik takipçi değil çünkü fixture DB'ye doğrudan yazıldı; aktör kendi bildirimini almaz
    assert not [n for n in emp.get("/notifications").json()["items"] if n["type"] == "TASK_PROGRESS"]

    assert watcher.delete(f"/tasks/{tid}/watch").status_code == 204
    assert _titles(watcher, watching="true") == set()


@ac("TASK-019/AC-3")
def test_progress_permissions(world: World, login) -> None:  # type: ignore[no-untyped-def]
    tid = _tid(world, "soc_todo")
    body = {"progress": 10, "note": "deneme", "version": 1}
    assert login("auditor").post(f"/tasks/{tid}/progress", json=body).status_code == 403
    assert login("analyst.soc3").post(f"/tasks/{tid}/progress", json=body).status_code == 403
    assert login("analyst.pentest1").post(f"/tasks/{tid}/progress", json=body).status_code == 404
    assert login("analyst.soc1").post(f"/tasks/{tid}/progress", json={**body, "note": " "}).status_code == 400
    assert (
        login("analyst.soc1").post(f"/tasks/{tid}/progress", json={**body, "progress": 101}).status_code
        == 400
    )
    assert login("unit.defense").post(f"/tasks/{tid}/progress", json=body).status_code == 200
    assert audit_actions("task.progress") == 1


@ac("TASK-019/AC-3")
def test_done_sets_progress_100_and_dashboard_average(world: World, login) -> None:  # type: ignore[no-untyped-def]
    mgr = login("manager.soc")
    tid = _tid(world, "soc_overdue")
    r = mgr.post(f"/tasks/{tid}/transitions", json={"to": "DONE", "version": 1})
    assert r.status_code == 200 and r.json()["progress"] == 100
    d = mgr.get("/dashboard/summary").json()
    soc = next(t for t in d["teams"] if t["teamName"] == "SOC")
    # SOC canlı task'ları: soc_todo 0, soc_overdue 100, soc_done 0 (fixture), soc_project 0 → ortalama 25
    assert soc["avgProgress"] == 25
    assert 0 <= d["avgProgress"] <= 100 and "mineAvgProgress" in d


# ------------------------------------------------------------------ ekler
@ac("TASK-019/AC-4")
def test_attachments_upload_download_and_rules(world: World, login) -> None:  # type: ignore[no-untyped-def]
    tid = _tid(world, "soc_todo")
    emp = login("analyst.soc1")
    files = {"file": ("rapor.txt", b"bulgu listesi", "text/plain")}
    r = emp.post(f"/tasks/{tid}/attachments", json=None, files=files)
    assert r.status_code == 201, r.text
    aid = r.json()["id"]
    assert emp.get(f"/tasks/{tid}").json()["attachmentCount"] == 1
    dl = emp.get(f"/attachments/{aid}")
    assert dl.status_code == 200 and dl.content == b"bulgu listesi"
    assert "attachment" in dl.headers["content-disposition"]
    assert login("analyst.pentest1").get(f"/attachments/{aid}").status_code == 404
    html = {"file": ("x.html", b"<script>", "text/html")}
    assert emp.post(f"/tasks/{tid}/attachments", json=None, files=html).status_code == 400
    assert login("auditor").post(f"/tasks/{tid}/attachments", json=None, files=files).status_code == 403
    assert login("analyst.soc2").delete(f"/attachments/{aid}").status_code == 403
    assert emp.delete(f"/attachments/{aid}").status_code == 204


# ------------------------------------------------------------------ yetkinlik puanı ve öneri
def _comp(name: str, cat: CompetencyCategory) -> Competency:
    with Session(OWNER, expire_on_commit=False) as db:
        cp = Competency(name=name, category=cat)
        db.add(cp)
        db.commit()
        return cp


@ac("TASK-019/AC-5")
def test_event_attendance_and_certification_raise_scores(world: World, login) -> None:  # type: ignore[no-untyped-def]
    malware = _comp("Zararlı Yazılım Analizi", CompetencyCategory.FORENSICS)
    with Session(OWNER) as db:
        db.add(
            UserCompetency(
                user_id=world.users["analyst.soc1"].id, competency_id=malware.id, level=3, score=60
            )
        )
        db.commit()
    d = login("director")
    start = datetime.now(UTC) - timedelta(days=3)
    ev = d.post(
        "/events",
        json={
            "title": "BlackHat Eğitimi",
            "type": "CONFERENCE",
            "scope": "CORPORATE",
            "startsAt": start.isoformat(),
            "endsAt": (start + timedelta(hours=8)).isoformat(),
            "notes": "Öne çıkanlar",
            "competencyIds": [str(malware.id)],
            "competencyPoints": 25,
        },
    )
    assert ev.status_code == 201, ev.text
    assert ev.json()["competencies"][0]["points"] == 25
    emp = login("analyst.soc1")
    p = emp.post(f"/events/{ev.json()['id']}/participations", json={"role": "ATTENDEE"}).json()
    mgr = login("manager.soc")
    assert mgr.patch(f"/participations/{p['id']}", json={"status": "APPROVED"}).status_code == 200
    assert mgr.patch(f"/participations/{p['id']}", json={"status": "ATTENDED"}).status_code == 200
    scores = {
        x["competency"]["name"]: x["score"]
        for x in emp.get(f"/users/{_uid(world, 'analyst.soc1')}/competencies").json()
    }
    assert scores["Zararlı Yazılım Analizi"] == 85
    assert any(n["type"] == "COMPETENCY_UPDATED" for n in emp.get("/notifications").json()["items"])

    cert = emp.post(
        f"/users/{_uid(world, 'analyst.soc1')}/certifications",
        json={
            "name": "GCFA",
            "issuedOn": str(date.today()),
            "competencyIds": [str(malware.id)],
            "points": 30,
        },
    )
    assert cert.status_code == 201, cert.text
    scores = {
        x["competency"]["name"]: x["score"]
        for x in emp.get(f"/users/{_uid(world, 'analyst.soc1')}/competencies").json()
    }
    assert scores["Zararlı Yazılım Analizi"] == 100  # en fazla 100
    assert (
        login("analyst.soc2")
        .post(
            f"/users/{_uid(world, 'analyst.soc1')}/certifications",
            json={"name": "CEH", "issuedOn": str(date.today())},
        )
        .status_code
        == 403
    )


@ac("TASK-019/AC-5")
def test_assignee_suggestion_ranks_by_competency(world: World, login) -> None:  # type: ignore[no-untyped-def]
    pt = _comp("Sızma Testi", CompetencyCategory.OFFENSIVE)
    grc = _comp("ISO 27001", CompetencyCategory.GRC)
    with Session(OWNER) as db:
        for key, comp, score in (
            ("analyst.soc1", pt, 40),
            ("analyst.soc2", pt, 90),
            ("analyst.soc3", grc, 95),
            ("analyst.pentest1", pt, 100),  # SOC yöneticisinin atama kapsamı dışında
        ):
            db.add(UserCompetency(user_id=world.users[key].id, competency_id=comp.id, level=3, score=score))
        db.commit()
    s = (
        login("manager.soc")
        .get("/tasks/assignee-suggestions", params={"category": "PENETRATION_TEST"})
        .json()
    )
    assert [x["user"]["fullName"] for x in s] == ["Analyst Soc2", "Analyst Soc1"]
    assert s[0]["score"] == 90 and s[0]["competencies"][0]["name"] == "Sızma Testi"


# ------------------------------------------------------------------ etkinlik fotoğrafları
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@ac("TASK-019/AC-5")
def test_event_photos(world: World, login) -> None:  # type: ignore[no-untyped-def]
    with Session(OWNER, expire_on_commit=False) as db:
        start = datetime.now(UTC) - timedelta(days=2)
        ev = Event(
            title="DEF CON",
            type=EventType.CONFERENCE,
            scope=EventScope.INDIVIDUAL,
            starts_at=start,
            ends_at=start + timedelta(hours=8),
            created_by=world.users["analyst.soc1"].id,
        )
        db.add(ev)
        db.flush()
        db.add(
            EventParticipation(
                event_id=ev.id,
                user_id=world.users["analyst.soc2"].id,
                role=ParticipationRole.ATTENDEE,
                status=ParticipationStatus.ATTENDED,
            )
        )
        db.commit()
    png = {"file": ("sahne.png", PNG, "image/png")}
    r = login("analyst.soc2").post(
        f"/events/{ev.id}/photos", json=None, files=png, data={"caption": "Açılış"}
    )
    assert r.status_code == 201, r.text
    assert login("analyst.soc1").get(f"/events/{ev.id}").json()["photoCount"] == 1
    img = login("analyst.pentest1").get(f"/event-photos/{r.json()['id']}")
    assert img.status_code == 200 and img.headers["content-type"] == "image/png"
    fake = {"file": ("x.png", b"not an image", "image/png")}
    assert login("analyst.soc1").post(f"/events/{ev.id}/photos", json=None, files=fake).status_code == 400
    assert login("analyst.soc3").post(f"/events/{ev.id}/photos", json=None, files=png).status_code == 403


# ------------------------------------------------------------------ planlı raporlar
@ac("TASK-019/AC-6")
def test_report_schedules(world: World, login, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    sent: list[tuple[str, str, list]] = []  # type: ignore[type-arg]
    monkeypatch.setattr(
        "app.email.sender.send",
        lambda to, subject, body, link=None, attachments=None: sent.append((to, subject, attachments)),
    )
    mgr = login("manager.soc")
    r = mgr.post(
        "/report-schedules", json={"name": "SOC haftalık", "frequency": "WEEKLY", "groupBy": "status"}
    )
    assert r.status_code == 201, r.text
    nxt = datetime.fromisoformat(r.json()["nextRunAt"])
    assert nxt > datetime.now(UTC) and nxt.astimezone().weekday() == 0
    m = mgr.post(
        "/report-schedules", json={"name": "Aylık", "frequency": "MONTHLY", "groupBy": "team"}
    ).json()
    assert datetime.fromisoformat(m["nextRunAt"]).day == 1
    assert mgr.post(f"/report-schedules/{r.json()['id']}/run").status_code == 202
    assert sent and sent[0][0] == "manager.soc@demo.local" and sent[0][2][0][0].endswith(".csv")
    assert mgr.get("/report-schedules").json()[0]["lastStatus"] == "SUCCESS"
    # Başkasının planı görünmez; çalışan planlayamaz
    assert login("manager.pentest").post(f"/report-schedules/{r.json()['id']}/run").status_code == 404
    assert (
        login("analyst.soc1")
        .post("/report-schedules", json={"name": "x y", "frequency": "WEEKLY", "groupBy": "status"})
        .status_code
        == 403
    )

    from app.modules.reports.schedules import run_due

    with Session(OWNER) as db:
        db.execute(text("UPDATE report_schedules SET next_run_at = now() - interval '1 minute'"))
        db.commit()
        assert run_due(db) == 2
        db.commit()
    assert len(sent) == 3


# ------------------------------------------------------------------ proje organizasyon ağacı
@ac("TASK-019/AC-7")
def test_project_organization_tree_and_stakeholders(world: World, login) -> None:  # type: ignore[no-untyped-def]
    pid = str(world.projects["soc"].id)
    mgr = login("manager.soc")
    assert (
        mgr.post(
            f"/projects/{pid}/stakeholders", json={"userId": _uid(world, "unit.defense"), "role": "SPONSOR"}
        ).status_code
        == 201
    )
    ext = mgr.post(
        f"/projects/{pid}/stakeholders",
        json={"name": "BT Altyapı", "organization": "BT", "role": "STAKEHOLDER"},
    )
    assert ext.status_code == 201
    assert mgr.post(f"/projects/{pid}/stakeholders", json={"role": "OBSERVER"}).status_code == 400
    assert (
        login("analyst.soc1")
        .post(f"/projects/{pid}/stakeholders", json={"name": "X Y", "role": "OBSERVER"})
        .status_code
        == 403
    )

    org = login("analyst.soc1").get(f"/projects/{pid}/organization").json()
    root = org["tree"][0]
    assert root["kind"] == "DIRECTOR"
    unit = next(n for n in root["children"] if n["kind"] == "UNIT")
    assert unit["name"] == "Savunma"
    um = next(n for n in unit["children"] if n["kind"] == "USER")
    assert um["name"] == "Unit Defense" and "Sponsor" in um["projectRoles"]
    team = next(n for n in unit["children"] if n["kind"] == "TEAM")
    people = {n["name"]: n["projectRoles"] for n in team["children"]}
    assert "Sorumlu" in people["Analyst Soc3"] and "Ekip yöneticisi" in people["Manager Soc"]
    assert {s["name"] for s in org["stakeholders"]} == {"Unit Defense", "BT Altyapı"}
    assert login("analyst.pentest1").get(f"/projects/{pid}/organization").status_code == 404
    assert mgr.delete(f"/projects/{pid}/stakeholders/{ext.json()['id']}").status_code == 204


# ------------------------------------------------------------------ unit yönetimi
@ac("TASK-019/AC-1")
def test_units_admin(world: World, login) -> None:  # type: ignore[no-untyped-def]
    d = login("director")
    units = d.get("/units").json()
    assert units[0]["name"] == "Savunma" and units[0]["teamCount"] == 2
    r = d.post("/units", json={"name": "Ofansif"})
    assert r.status_code == 201
    assert (
        d.patch(f"/teams/{world.teams['pentest'].id}", json={"unitId": r.json()["id"]}).json()["unitName"]
        == "Ofansif"
    )
    assert (
        d.patch(f"/units/{r.json()['id']}", json={"managerId": _uid(world, "manager.soc")}).status_code == 400
    )
    assert login("manager.soc").post("/units", json={"name": "Yetkisiz"}).status_code == 403
