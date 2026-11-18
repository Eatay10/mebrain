"""TSK-01..08, PRJ-01: task yaşam döngüsü, doğrulama, yorum ve bildirimler."""

from tests.conftest import World, audit_actions


def _new(api, world: World, **kw):  # type: ignore[no-untyped-def]
    body = {"type": "STANDARD", "title": "Yeni task", "teamId": str(world.teams["soc"].id), **kw}
    return api.post("/tasks", json=body)


def test_manager_creates_task_with_assignment_notifications(world: World, login) -> None:  # type: ignore[no-untyped-def]
    mgr = login("manager.soc")
    r = _new(
        mgr,
        world,
        assigneeId=str(world.users["analyst.soc1"].id),
        backupAssigneeId=str(world.users["analyst.soc2"].id),
        priority="HIGH",
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "TODO" and r.json()["version"] == 1
    assert audit_actions("task.create") == 1
    n1 = login("analyst.soc1").get("/notifications").json()["items"]
    n2 = login("analyst.soc2").get("/notifications").json()["items"]
    assert n1[0]["type"] == "TASK_ASSIGNED" and n2[0]["type"] == "TASK_BACKUP_ASSIGNED"


def test_backup_cannot_equal_assignee_and_must_be_team_member(world: World, login) -> None:  # type: ignore[no-untyped-def]
    mgr = login("manager.soc")
    same = str(world.users["analyst.soc1"].id)
    assert _new(mgr, world, assigneeId=same, backupAssigneeId=same).status_code == 400
    assert _new(mgr, world, assigneeId=str(world.users["analyst.pentest1"].id)).status_code == 400


def test_project_and_standard_type_rules(world: World, login) -> None:  # type: ignore[no-untyped-def]
    mgr = login("manager.soc")
    assert mgr.post("/tasks", json={"type": "PROJECT", "title": "Projesiz"}).status_code == 400
    assert _new(mgr, world, projectId=str(world.projects["soc"].id)).status_code == 400
    r = mgr.post(
        "/tasks", json={"type": "PROJECT", "title": "Proje task", "projectId": str(world.projects["soc"].id)}
    )
    assert r.status_code == 201 and r.json()["teamId"] == str(world.teams["soc"].id)
    assert r.json()["project"]["name"] == "SIEM Yenileme"


def test_employee_creates_only_self_assigned_standard_in_own_team(world: World, login) -> None:  # type: ignore[no-untyped-def]
    emp = login("analyst.soc1")
    assert emp.post("/tasks", json={"type": "STANDARD", "title": "Kendi işim"}).status_code == 201
    other = str(world.users["analyst.soc2"].id)
    assert _new(emp, world, assigneeId=other).status_code == 403
    r = emp.post(
        "/tasks", json={"type": "PROJECT", "title": "Proje işi", "projectId": str(world.projects["soc"].id)}
    )
    assert r.status_code == 403


def test_transition_lifecycle_sets_timestamps(world: World, login) -> None:  # type: ignore[no-untyped-def]
    emp = login("analyst.soc1")
    t = world.tasks["soc_todo"]
    r = emp.post(f"/tasks/{t.id}/transitions", json={"to": "IN_PROGRESS", "version": 1})
    assert r.status_code == 200 and r.json()["startedAt"] and r.json()["version"] == 2
    r = emp.post(f"/tasks/{t.id}/transitions", json={"to": "DONE", "version": 2})
    assert r.status_code == 200 and r.json()["completedAt"]
    assert login("manager.soc").get("/notifications").json()["total"] >= 1


def test_invalid_transitions(world: World, login) -> None:  # type: ignore[no-untyped-def]
    emp = login("analyst.soc1")
    t = world.tasks["soc_todo"]
    assert emp.post(f"/tasks/{t.id}/transitions", json={"to": "DONE", "version": 1}).status_code == 422
    assert emp.post(f"/tasks/{t.id}/transitions", json={"to": "BLOCKED", "version": 1}).status_code == 400
    assert emp.post(f"/tasks/{t.id}/transitions", json={"to": "IN_PROGRESS", "version": 9}).status_code == 409


def test_backup_assignee_can_transition_but_other_employee_cannot(world: World, login) -> None:  # type: ignore[no-untyped-def]
    t = world.tasks["soc_todo"]
    assert (
        login("analyst.soc3")
        .post(f"/tasks/{t.id}/transitions", json={"to": "IN_PROGRESS", "version": 1})
        .status_code
        == 403
    )
    assert (
        login("analyst.soc2")
        .post(f"/tasks/{t.id}/transitions", json={"to": "IN_PROGRESS", "version": 1})
        .status_code
        == 200
    )


def test_reopen_done_only_manager(world: World, login) -> None:  # type: ignore[no-untyped-def]
    t = world.tasks["soc_done"]
    assert (
        login("analyst.soc2")
        .post(f"/tasks/{t.id}/transitions", json={"to": "IN_PROGRESS", "version": 1})
        .status_code
        == 403
    )
    r = login("manager.soc").post(f"/tasks/{t.id}/transitions", json={"to": "IN_PROGRESS", "version": 1})
    assert r.status_code == 200 and r.json()["completedAt"] is None


def test_comments_and_history(world: World, login) -> None:  # type: ignore[no-untyped-def]
    t = world.tasks["soc_todo"]
    mgr = login("manager.soc")
    r = mgr.post(f"/tasks/{t.id}/comments", json={"body": "<script>alert(1)</script> incele"})
    assert r.status_code == 201
    assert mgr.get(f"/tasks/{t.id}/comments").json()["total"] == 1
    assert (
        login("analyst.soc1").get("/notifications?unread=true").json()["items"][0]["type"] == "TASK_COMMENTED"
    )
    history = mgr.get(f"/tasks/{t.id}/history").json()
    assert [h["action"] for h in history] == ["comment.create"]


def test_list_filters_and_sort_validation(world: World, login) -> None:  # type: ignore[no-untyped-def]
    emp = login("analyst.soc1")
    r = emp.get("/tasks?assigneeId=me&status=TODO,IN_PROGRESS&overdue=true")
    assert [t["title"] for t in r.json()["items"]] == ["soc_overdue"]
    assert emp.get("/tasks?sort=title;DROP").status_code == 400
    assert emp.get("/tasks?status=NOPE").status_code == 400
    assert emp.get("/tasks?q=%25").json()["total"] == 0  # LIKE joker karakteri kaçışlı
    assert emp.get("/tasks?recurring=true").json()["total"] == 1


def test_delete_task_and_project_conflict(world: World, login) -> None:  # type: ignore[no-untyped-def]
    mgr = login("manager.soc")
    assert login("analyst.soc1").delete(f"/tasks/{world.tasks['soc_todo'].id}").status_code == 403
    assert mgr.delete(f"/projects/{world.projects['soc'].id}").status_code == 409
    assert mgr.delete(f"/tasks/{world.tasks['soc_project'].id}").status_code == 204
    assert mgr.delete(f"/projects/{world.projects['soc'].id}").status_code == 204
    assert mgr.get(f"/tasks/{world.tasks['soc_project'].id}").status_code == 404


def test_project_crud_scope(world: World, login) -> None:  # type: ignore[no-untyped-def]
    mgr = login("manager.soc")
    r = mgr.post("/projects", json={"teamId": str(world.teams["vuln"].id), "name": "Yama Kampanyası"})
    assert r.status_code == 201
    assert (
        mgr.post(
            "/projects", json={"teamId": str(world.teams["vuln"].id), "name": "Yama Kampanyası"}
        ).status_code
        == 409
    )
    assert (
        mgr.post("/projects", json={"teamId": str(world.teams["pentest"].id), "name": "X1"}).status_code
        == 404
    )
    assert (
        login("analyst.soc1")
        .post("/projects", json={"teamId": str(world.teams["soc"].id), "name": "X2"})
        .status_code
        == 403
    )
    p = mgr.get(f"/projects/{world.projects['soc'].id}").json()
    assert p["progress"]["blocked"] == 1 and p["progress"]["total"] == 1
