"""DSH-01..03, RPT-01..02, T08, T11."""

from datetime import date, timedelta

from tests.conftest import World, security_events


def _sum(c: dict) -> int:  # type: ignore[type-arg]
    return c["todo"] + c["inProgress"] + c["blocked"] + c["done"]


def test_dashboard_counts_invariants_and_standard_project_split(world: World, login) -> None:  # type: ignore[no-untyped-def]
    d = login("director").get("/dashboard/summary").json()
    assert len(d["teams"]) == 3
    soc = next(t for t in d["teams"] if t["teamName"] == "SOC")
    assert soc["all"]["total"] == 4  # şablon sayılmaz
    assert soc["standard"]["total"] == 3 and soc["project"]["total"] == 1
    assert soc["all"]["overdue"] == 1 and soc["all"]["blocked"] == 1
    for t in d["teams"]:
        for part in ("all", "standard", "project"):
            assert _sum(t[part]) == t[part]["total"]
        assert t["all"]["total"] == t["standard"]["total"] + t["project"]["total"]
    assert d["totals"]["all"]["total"] == 6


def test_dashboard_matches_task_list_counts(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("manager.soc")
    soc_id = str(world.teams["soc"].id)
    d = api.get("/dashboard/summary").json()
    soc = next(t for t in d["teams"] if t["teamId"] == soc_id)
    listed = api.get(f"/tasks?teamId={soc_id}&status=TODO,IN_PROGRESS,BLOCKED,DONE&pageSize=100").json()[
        "total"
    ]
    assert listed == soc["all"]["total"]


def test_dashboard_scope_per_role(world: World, login) -> None:  # type: ignore[no-untyped-def]
    assert len(login("analyst.soc1").get("/dashboard/summary").json()["teams"]) == 1
    assert len(login("manager.soc").get("/dashboard/summary").json()["teams"]) == 2
    emp = login("analyst.soc1")
    assert emp.get(f"/dashboard/summary?teamId={world.teams['pentest'].id}").status_code == 404
    assert emp.get("/dashboard/summary").json()["mine"]["total"] == 2


def test_report_group_by_assignee_totals(world: World, login) -> None:  # type: ignore[no-untyped-def]
    today = date.today()
    r = login("director").get(f"/reports/tasks?groupBy=assignee&from={today - timedelta(days=7)}&to={today}")
    assert r.status_code == 200
    body = r.json()
    assert sum(row["counts"]["total"] for row in body["rows"]) == body["totals"]["total"] == 6


def test_report_validation(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("director")
    today = date.today()
    assert (
        api.get(f"/reports/tasks?groupBy=team&from={today}&to={today - timedelta(days=1)}").status_code == 400
    )
    assert (
        api.get(f"/reports/tasks?groupBy=team&from={today - timedelta(days=400)}&to={today}").status_code
        == 400
    )
    assert api.get(f"/reports/tasks?groupBy=nope&from={today}&to={today}").status_code == 400


def test_employee_report_limited_to_own_team(world: World, login) -> None:  # type: ignore[no-untyped-def]
    today = date.today()
    rows = login("analyst.soc1").get(f"/reports/tasks?groupBy=team&from={today}&to={today}").json()["rows"]
    assert [r["label"] for r in rows] == ["SOC"]


def test_csv_export_neutralizes_formulas_and_logs_bulk_export(world: World, login) -> None:  # type: ignore[no-untyped-def]
    mgr = login("manager.soc")
    mgr.post("/projects", json={"teamId": str(world.teams["soc"].id), "name": '=HYPERLINK("http://x")'})
    pid = mgr.get("/projects?q=HYPERLINK").json()["items"][0]["id"]
    mgr.post("/tasks", json={"type": "PROJECT", "title": "csv", "projectId": pid})
    today = date.today()
    r = mgr.get(f"/reports/tasks?groupBy=project&from={today}&to={today}&format=csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert r.content.startswith("﻿".encode())
    assert "'=HYPERLINK" in r.text and "\n=HYPERLINK" not in r.text
    assert security_events("BULK_EXPORT") == 1


def test_page_size_limit(world: World, login) -> None:  # type: ignore[no-untyped-def]
    assert login("director").get("/tasks?pageSize=1000").status_code == 400
