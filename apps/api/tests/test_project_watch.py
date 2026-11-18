"""Projeye yıldız koyma (takip)."""

from tests.conftest import World


def test_star_and_unstar_project(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("analyst.soc1")
    pid = world.projects["soc"].id
    assert api.get(f"/projects/{pid}").json()["isWatching"] is False
    assert api.put(f"/projects/{pid}/watch").status_code == 204
    assert api.put(f"/projects/{pid}/watch").status_code == 204  # idempotent
    assert api.get(f"/projects/{pid}").json()["isWatching"] is True
    items = api.get("/projects?watching=true").json()["items"]
    assert [p["id"] for p in items] == [str(pid)]
    # yıldız kişiseldir
    assert login("manager.soc").get(f"/projects/{pid}").json()["isWatching"] is False
    assert api.delete(f"/projects/{pid}/watch").status_code == 204
    assert api.get("/projects?watching=true").json()["items"] == []


def test_cannot_star_project_out_of_scope(world: World, login) -> None:  # type: ignore[no-untyped-def]
    r = login("analyst.soc1").put(f"/projects/{world.projects['pentest'].id}/watch")
    assert r.status_code == 404


def test_auditor_can_star(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("auditor")
    assert api.put(f"/projects/{world.projects['pentest'].id}/watch").status_code == 204


def test_star_requires_csrf(world: World, login) -> None:  # type: ignore[no-untyped-def]
    api = login("analyst.soc1")
    r = api.put(f"/projects/{world.projects['soc'].id}/watch", headers={"X-CSRF-Token": "yanlis"})
    assert r.status_code == 403
