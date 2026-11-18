"""AUT-02, AUT-04, T04, T05: kapsam, IDOR, alan seviyesi yetki, rol değişikliği, denetmen."""

from tests.conftest import World, audit_actions, security_events


def test_employee_cannot_read_other_team_task_gets_404(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("analyst.soc1")
    r = api.get(f"/tasks/{world.tasks['pentest_todo'].id}")
    assert r.status_code == 404
    assert security_events("NOT_FOUND_PROBE") == 1


def test_employee_list_only_own_team(world: World, login) -> None:  # type: ignore[no-untyped-def]
    items = login("analyst.soc1").get("/tasks?pageSize=100").json()["items"]
    assert items and {t["teamId"] for t in items} == {str(world.teams["soc"].id)}


def test_manager_sees_managed_teams_only(world: World, login) -> None:  # type: ignore[no-untyped-def]
    teams = {t["teamId"] for t in login("manager.soc").get("/tasks?pageSize=100").json()["items"]}
    assert teams == {str(world.teams["soc"].id), str(world.teams["vuln"].id)}


def test_employee_cannot_reassign_task(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("analyst.soc1")
    t = world.tasks["soc_todo"]
    r = api.patch(f"/tasks/{t.id}", json={"version": 1, "assigneeId": str(world.users["analyst.soc2"].id)})
    assert r.status_code == 403
    assert security_events("AUTHZ_DENIED") == 1


def test_mass_assignment_unknown_fields_rejected(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("manager.soc")
    r = api.patch(
        f"/tasks/{world.tasks['soc_todo'].id}", json={"version": 1, "teamId": str(world.teams["pentest"].id)}
    )
    assert r.status_code == 400


def test_manager_cannot_update_unmanaged_team_task(world: World, login) -> None:  # type: ignore[no-untyped-def]
    r = login("manager.soc").patch(
        f"/tasks/{world.tasks['pentest_todo'].id}", json={"version": 1, "title": "Hack"}
    )
    assert r.status_code == 404


def test_auditor_reads_everything_but_cannot_write(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("auditor")
    assert api.get("/tasks?pageSize=100").json()["total"] == 6
    assert api.get("/audit-logs").status_code == 200
    assert api.get("/security/summary").status_code == 200
    t = world.tasks["soc_todo"]
    assert api.post(f"/tasks/{t.id}/transitions", json={"to": "IN_PROGRESS", "version": 1}).status_code == 403
    assert api.post(f"/tasks/{t.id}/comments", json={"body": "denetim notu"}).status_code == 403
    r = api.post(
        "/tasks", json={"type": "STANDARD", "title": "Denetmen task", "teamId": str(world.teams["soc"].id)}
    )
    assert r.status_code == 403


def test_only_director_changes_roles_and_not_own(world: World, login) -> None:  # type: ignore[no-untyped-def]
    target = str(world.users["analyst.soc1"].id)
    assert login("manager.soc").patch(f"/users/{target}", json={"role": "MANAGER"}).status_code == 403
    director = login("director")
    r = director.patch(f"/users/{target}", json={"role": "AUDITOR"})
    assert r.status_code == 200 and r.json()["role"] == "AUDITOR" and r.json()["teamId"] is None
    assert security_events("ROLE_CHANGED") == 1
    assert audit_actions("user.role_change") == 1
    me = str(world.users["director"].id)
    assert director.patch(f"/users/{me}", json={"role": "EMPLOYEE"}).status_code == 403


def test_employee_and_manager_cannot_read_security(world: World, login) -> None:  # type: ignore[no-untyped-def]
    for key in ("analyst.soc1", "manager.soc"):
        api = login(key)
        assert api.get("/security/events").status_code == 403
        assert api.get("/system/metrics-summary").status_code == 403
    assert login("analyst.soc1").get("/audit-logs").status_code == 403


def test_audit_log_is_append_only_for_app_role(world: World, login) -> None:  # type: ignore[no-untyped-def]
    import pytest
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import ProgrammingError

    from app.config import get_settings

    login("analyst.soc1")
    engine = create_engine(get_settings().database_url)  # uygulama rolü (cth_app)
    with engine.connect() as conn, pytest.raises(ProgrammingError, match="permission denied"):
        conn.execute(text("UPDATE audit_logs SET action = 'tampered'"))
