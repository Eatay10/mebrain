"""Raporda unit gruplaması ve unit filtresi."""

from datetime import date, timedelta

import pytest

from tests.conftest import World

RANGE = f"from={date.today() - timedelta(days=30)}&to={date.today()}"


def _rows(api, q: str) -> dict[str, int]:  # type: ignore[no-untyped-def]
    r = api.get(f"/reports/tasks?{RANGE}&{q}")
    assert r.status_code == 200, r.text
    return {row["label"]: row["counts"]["total"] for row in r.json()["rows"]}


@pytest.mark.ac("TASK-019/AC-1")
def test_director_groups_report_by_unit(world: World, login) -> None:  # type: ignore[no-untyped-def]
    assert _rows(login("director"), "groupBy=unit") == {"Savunma": 5, "Unit'e bağlı olmayan ekipler": 1}


@pytest.mark.ac("TASK-019/AC-1")
def test_unit_filter_narrows_team_grouping(world: World, login) -> None:  # type: ignore[no-untyped-def]
    rows = _rows(login("director"), f"groupBy=team&unitId={world.units['defense'].id}")
    assert set(rows) == {"SOC", "Zafiyet"}


@pytest.mark.ac("TASK-019/AC-1")
def test_unit_manager_sees_only_own_unit(world: World, login) -> None:  # type: ignore[no-untyped-def]
    assert _rows(login("unit.defense"), "groupBy=unit") == {"Savunma": 5}


@pytest.mark.ac("TASK-019/AC-1")
def test_unit_filter_out_of_scope_is_404(world: World, login) -> None:  # type: ignore[no-untyped-def]
    r = login("analyst.pentest1").get(
        f"/reports/tasks?{RANGE}&groupBy=team&unitId={world.units['defense'].id}"
    )
    assert r.status_code == 404


def test_unit_group_csv(world: World, login) -> None:  # type: ignore[no-untyped-def]
    r = login("director").get(f"/reports/tasks?{RANGE}&groupBy=unit&format=csv")
    assert r.status_code == 200 and "Savunma" in r.text
