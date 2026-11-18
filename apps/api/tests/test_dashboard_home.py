"""Genel bakış kartları: bugünkü görevler, onay bekleyenler, yedeği eksik görevler; hasBackup filtresi."""

from datetime import UTC, datetime, timedelta

from tests.conftest import World


def _summary(login, who: str) -> dict:  # type: ignore[no-untyped-def,type-arg]
    r = login(who).get("/dashboard/summary")
    assert r.status_code == 200, r.text
    return r.json()


def test_today_counts_own_tasks_due_today(world: World, login) -> None:  # type: ignore[no-untyped-def]
    assert _summary(login, "analyst.vuln1")["today"] == {"total": 1, "done": 0}
    assert _summary(login, "analyst.soc1")["today"] == {"total": 0, "done": 0}
    # yönetici rolleri kapsamlarındaki bugünkü task'ları görür (vuln_todo)
    assert _summary(login, "manager.soc")["today"] == {"total": 1, "done": 0}
    assert _summary(login, "manager.pentest")["today"] == {"total": 0, "done": 0}


def test_missing_backup_only_for_managing_roles(world: World, login) -> None:  # type: ignore[no-untyped-def]
    assert _summary(login, "analyst.soc1")["missingBackup"] == 0
    # soc_overdue, soc_project, vuln_todo yedeksiz ve açık; soc_done kapalı, soc_todo'nun yedeği var
    assert _summary(login, "manager.soc")["missingBackup"] == 3
    assert _summary(login, "unit.defense")["missingBackup"] == 3
    assert _summary(login, "director")["missingBackup"] == 4  # + pentest_todo


def test_has_backup_filter(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("manager.soc")
    without = {t["title"] for t in api.get("/tasks?hasBackup=false&pageSize=100").json()["items"]}
    assert without == {"soc_overdue", "soc_done", "soc_project", "vuln_todo"}
    with_ = {t["title"] for t in api.get("/tasks?hasBackup=true&pageSize=100").json()["items"]}
    assert with_ == {"soc_todo"}


def test_pending_approvals_per_role(world: World, login) -> None:  # type: ignore[no-untyped-def]
    emp = login("analyst.soc1")
    starts = datetime.now(UTC) + timedelta(days=10)
    ev = emp.post(
        "/events",
        json={
            "title": "Eğitim",
            "type": "TRAINING",
            "scope": "INDIVIDUAL",
            "startsAt": starts.isoformat(),
            "endsAt": (starts + timedelta(hours=4)).isoformat(),
        },
    )
    assert ev.status_code == 201, ev.text
    r = emp.post(f"/events/{ev.json()['id']}/participations", json={"role": "ATTENDEE"})
    assert r.status_code in (200, 201), r.text
    assert _summary(login, "analyst.soc1")["approvals"]["pending"] == 1
    assert _summary(login, "manager.soc")["approvals"]["pending"] == 1
    assert _summary(login, "manager.pentest")["approvals"]["pending"] == 0
    assert _summary(login, "director")["approvals"]["pending"] == 1
