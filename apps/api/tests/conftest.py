"""Test altyapısı: ayrı test veritabanı, her testte temiz küçük dünya, rol başına istemci.

Uygulama en az yetkili `cth_app` rolüyle bağlanır (gerçek ortamla aynı); migration ve temizlik owner ile.
"""

import os
import secrets
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

_ENV = Path(__file__).resolve().parents[3] / ".env"


def _dotenv() -> dict[str, str]:
    out: dict[str, str] = {}
    if _ENV.exists():
        for line in _ENV.read_text().splitlines():
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    return out


def _test_db(url: str) -> str:
    base, _, name = url.rpartition("/")
    return f"{base}/{name.split('?')[0]}_test"


_env = {**_dotenv(), **os.environ}
os.environ["DATABASE_URL"] = _test_db(_env["DATABASE_URL"])
os.environ["MIGRATION_DATABASE_URL"] = _test_db(_env["MIGRATION_DATABASE_URL"])
os.environ.update(
    {
        "CTH_ENV": "test",
        "CTH_COOKIE_SECURE": "false",
        "CTH_RATE_ANON": "100000",
        "CTH_RATE_AUTH": "100000",
        "CTH_RATE_LOGIN": "100000",
        "CTH_CORS_ORIGINS": "",
    }
)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.auth.passwords import hash_password  # noqa: E402
from app.contract import Recurrence, Role, TaskStatus, TaskType  # noqa: E402
from app.core.ratelimit import limiter  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Project, Task, Team, Unit, User  # noqa: E402
from app.seed.__main__ import TABLES  # noqa: E402

PASSWORD = secrets.token_urlsafe(18)  # her test çalışmasında rastgele
_HASH = hash_password(PASSWORD)
OWNER = create_engine(os.environ["MIGRATION_DATABASE_URL"])
API = "/api/v1"
CLIENT_ADDR = ("203.0.113.10", 50000)  # TEST-NET-3 (RFC 5737)


@pytest.fixture(scope="session", autouse=True)
def _migrate() -> None:
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "migrations"))
    cfg.set_main_option("sqlalchemy.url", os.environ["MIGRATION_DATABASE_URL"])
    command.upgrade(cfg, "head")


@dataclass
class World:
    teams: dict[str, Team] = field(default_factory=dict)
    units: dict[str, Unit] = field(default_factory=dict)
    users: dict[str, User] = field(default_factory=dict)
    projects: dict[str, Project] = field(default_factory=dict)
    tasks: dict[str, Task] = field(default_factory=dict)


def _user(db: Session, w: World, key: str, role: Role, team: str | None) -> None:
    u = User(
        email=f"{key}@demo.local",
        full_name=key.replace(".", " ").title(),
        role=role,
        team_id=w.teams[team].id if team else None,
        password_hash=_HASH,
    )
    db.add(u)
    w.users[key] = u


@pytest.fixture
def world() -> Iterator[World]:
    """Üç ekip (soc, pentest, vuln); SOC yöneticisi 'vuln' ekibini de yönetir.

    'defense' unit'i soc + vuln ekiplerini kapsar (unit yöneticisi: unit.defense); pentest bir unit'e bağlı değil.
    """
    limiter.reset()
    with Session(OWNER, expire_on_commit=False) as db:
        db.execute(text("UPDATE teams SET manager_id = NULL"))
        db.execute(text("UPDATE units SET manager_id = NULL"))
        db.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))
        w = World()
        for key, name in (("soc", "SOC"), ("pentest", "Pentest"), ("vuln", "Zafiyet")):
            w.teams[key] = Team(name=name)
            db.add(w.teams[key])
        db.flush()
        _user(db, w, "director", Role.DIRECTOR, None)
        _user(db, w, "auditor", Role.AUDITOR, None)
        _user(db, w, "unit.defense", Role.UNIT_MANAGER, None)
        _user(db, w, "manager.soc", Role.MANAGER, "soc")
        _user(db, w, "manager.pentest", Role.MANAGER, "pentest")
        for i in (1, 2, 3):
            _user(db, w, f"analyst.soc{i}", Role.EMPLOYEE, "soc")
        _user(db, w, "analyst.pentest1", Role.EMPLOYEE, "pentest")
        _user(db, w, "analyst.vuln1", Role.EMPLOYEE, "vuln")
        db.flush()
        w.teams["soc"].manager_id = w.users["manager.soc"].id
        w.teams["vuln"].manager_id = w.users["manager.soc"].id
        w.teams["pentest"].manager_id = w.users["manager.pentest"].id
        w.units["defense"] = Unit(name="Savunma", manager_id=w.users["unit.defense"].id)
        db.add(w.units["defense"])
        db.flush()
        w.teams["soc"].unit_id = w.units["defense"].id
        w.teams["vuln"].unit_id = w.units["defense"].id
        w.projects["soc"] = Project(team_id=w.teams["soc"].id, name="SIEM Yenileme")
        w.projects["pentest"] = Project(team_id=w.teams["pentest"].id, name="Dış Test")
        db.add_all(w.projects.values())
        db.flush()
        today = date.today()

        def task(key: str, team: str, **kw: Any) -> None:
            t = Task(
                team_id=w.teams[team].id,
                type=kw.pop("type", TaskType.STANDARD),
                title=kw.pop("title", key),
                created_by=w.users[f"manager.{'soc' if team != 'pentest' else 'pentest'}"].id,
                **kw,
            )
            db.add(t)
            w.tasks[key] = t

        task(
            "soc_todo",
            "soc",
            assignee_id=w.users["analyst.soc1"].id,
            backup_assignee_id=w.users["analyst.soc2"].id,
            due_date=today + timedelta(days=5),
        )
        task(
            "soc_overdue",
            "soc",
            assignee_id=w.users["analyst.soc1"].id,
            due_date=today - timedelta(days=2),
            status=TaskStatus.IN_PROGRESS,
        )
        task(
            "soc_done",
            "soc",
            assignee_id=w.users["analyst.soc2"].id,
            status=TaskStatus.DONE,
            due_date=today - timedelta(days=10),
        )
        task(
            "soc_project",
            "soc",
            type=TaskType.PROJECT,
            project_id=w.projects["soc"].id,
            assignee_id=w.users["analyst.soc3"].id,
            status=TaskStatus.BLOCKED,
            blocked_reason="Erişim bekleniyor",
        )
        task(
            "soc_template",
            "soc",
            recurrence=Recurrence.DAILY,
            assignee_id=w.users["analyst.soc1"].id,
            created_at=datetime.now(UTC) - timedelta(days=30),
        )
        task("pentest_todo", "pentest", assignee_id=w.users["analyst.pentest1"].id)
        task("vuln_todo", "vuln", assignee_id=w.users["analyst.vuln1"].id, due_date=today)
        db.commit()
        yield w


class Api:
    """Oturum açmış istemci; durum değiştiren isteklere CSRF header'ını otomatik ekler."""

    def __init__(self, client: TestClient, csrf: str | None = None, token: str | None = None) -> None:
        self.c, self.csrf, self.token = client, csrf, token

    def _h(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = dict(extra or {})
        if self.csrf:
            h.setdefault("X-CSRF-Token", self.csrf)
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def get(self, path: str, **kw: Any) -> Any:
        return self.c.get(API + path, headers=self._h(kw.pop("headers", None)), **kw)

    def post(self, path: str, json: Any = None, **kw: Any) -> Any:
        return self.c.post(API + path, json=json, headers=self._h(kw.pop("headers", None)), **kw)

    def patch(self, path: str, json: Any = None, **kw: Any) -> Any:
        return self.c.patch(API + path, json=json, headers=self._h(kw.pop("headers", None)), **kw)

    def put(self, path: str, json: Any = None, **kw: Any) -> Any:
        return self.c.put(API + path, json=json, headers=self._h(kw.pop("headers", None)), **kw)

    def delete(self, path: str, **kw: Any) -> Any:
        return self.c.delete(API + path, headers=self._h(kw.pop("headers", None)), **kw)


@pytest.fixture
def anon() -> TestClient:
    return TestClient(app, client=CLIENT_ADDR)


@pytest.fixture
def login(world: World) -> Callable[[str], Api]:
    def _login(key: str) -> Api:
        client = TestClient(app, client=CLIENT_ADDR)
        r = client.post(f"{API}/auth/login", json={"email": f"{key}@demo.local", "password": PASSWORD})
        assert r.status_code == 200, r.text
        return Api(client, r.json()["csrfToken"])

    return _login


def security_events(event_type: str) -> int:
    with OWNER.connect() as conn:
        return conn.execute(
            text("SELECT count(*) FROM security_events WHERE type = :t"), {"t": event_type}
        ).scalar()


def audit_actions(action: str) -> int:
    with OWNER.connect() as conn:
        return conn.execute(text("SELECT count(*) FROM audit_logs WHERE action = :a"), {"a": action}).scalar()
