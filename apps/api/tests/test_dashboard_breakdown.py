"""Dashboard kırılımı rolüne göre: çalışan → yok, yönetici → çalışanlar, unit yöneticisi → ekip yöneticileri
(puanla), direktör/denetmen → unit'ler."""

import pytest

from app import contract as c
from app.modules.dashboard.service import score
from tests.conftest import World


def _bd(login, who: str) -> dict:  # type: ignore[no-untyped-def,type-arg]
    r = login(who).get("/dashboard/summary")
    assert r.status_code == 200, r.text
    return r.json()["breakdown"]


@pytest.mark.ac("TASK-019/AC-1")
def test_employee_has_no_team_breakdown(world: World, login) -> None:  # type: ignore[no-untyped-def]
    assert _bd(login, "analyst.soc1") == {"kind": "NONE", "rows": []}


@pytest.mark.ac("TASK-019/AC-1")
def test_manager_sees_status_per_member(world: World, login) -> None:  # type: ignore[no-untyped-def]
    bd = _bd(login, "manager.soc")
    assert bd["kind"] == "MEMBER"
    rows = {r["assigneeId"]: r for r in bd["rows"]}
    expected = {"analyst.soc1", "analyst.soc2", "analyst.soc3", "analyst.vuln1"}
    assert set(rows) == {str(world.users[k].id) for k in expected}
    soc1 = rows[str(world.users["analyst.soc1"].id)]
    assert soc1["all"]["total"] == 2 and soc1["all"]["overdue"] == 1
    assert soc1["teamId"] == str(world.teams["soc"].id)
    # başka ekibin çalışanı (pentest) görünmez
    assert str(world.users["analyst.pentest1"].id) not in rows


@pytest.mark.ac("TASK-019/AC-1")
def test_unit_manager_sees_each_team_manager_with_score(world: World, login) -> None:  # type: ignore[no-untyped-def]
    bd = _bd(login, "unit.defense")
    assert bd["kind"] == "TEAM_MANAGER"
    by_team = {r["teamId"]: r for r in bd["rows"]}
    assert set(by_team) == {str(world.teams["soc"].id), str(world.teams["vuln"].id)}
    soc = by_team[str(world.teams["soc"].id)]
    assert soc["label"] == world.users["manager.soc"].full_name and soc["sublabel"] == "SOC"
    assert soc["all"]["total"] == 4
    assert all(0 <= r["score"] <= 100 for r in bd["rows"])
    scores = [r["score"] for r in bd["rows"]]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.ac("TASK-019/AC-1")
@pytest.mark.parametrize("who", ["director", "auditor"])
def test_director_and_auditor_see_units(world: World, login, who: str) -> None:  # type: ignore[no-untyped-def]
    bd = _bd(login, who)
    assert bd["kind"] == "UNIT"
    rows = {r["label"]: r["all"]["total"] for r in bd["rows"]}
    assert rows == {"Savunma": 5, "Unit'e bağlı olmayan ekipler": 1}


def test_score_formula() -> None:
    def sc(done: int, overdue: int, total: int) -> c.StatusCounts:
        return c.StatusCounts(
            todo=total - done, in_progress=0, blocked=0, done=done, overdue=overdue, total=total
        )

    assert score(sc(0, 0, 0), 0) == 0
    assert score(sc(10, 0, 10), 100) == 100
    assert score(sc(5, 0, 10), 60) == 55  # 0,5×50 + 0,5×60
    assert score(sc(0, 10, 10), 0) == 0  # negatife düşmez
