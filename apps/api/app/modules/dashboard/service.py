"""Dashboard özeti — ekip × tür durum sayıları (DSH-01..03) ve role göre kırılım.

Kırılım (breakdown) kullanıcının rolüne göre seçilir:
- EMPLOYEE → yok (ekip kırılımı gösterilmez)
- MANAGER → yönettiği ekiplerin çalışanları (sorumlu bazında)
- UNIT_MANAGER → unit'indeki her ekip, ekip yöneticisiyle ayrı satır (performans puanıyla)
- DIRECTOR / AUDITOR → unit bazında
"""

from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.scope import in_scope, involved_filter, managed_team_ids, team_filter, visible_team_ids
from app.contract import DashboardBreakdownKind as BK
from app.contract import ParticipationStatus, ProjectStatus, Role, TaskStatus, TaskType
from app.core.errors import NotFound
from app.models import EventParticipation, Project, Task, TaskWatcher, Team, Unit, User
from app.models.base import utcnow
from app.modules.projects.service import progress_for
from app.modules.tasks import counting

KIND_BY_ROLE = {
    Role.EMPLOYEE: BK.NONE,
    Role.MANAGER: BK.MEMBER,
    Role.UNIT_MANAGER: BK.TEAM_MANAGER,
    Role.DIRECTOR: BK.UNIT,
    Role.AUDITOR: BK.UNIT,
}


def score(counts: c.StatusCounts, avg_progress: float) -> int:
    """0,5 × tamamlanma oranı + 0,5 × ortalama ilerleme − gecikmiş oranı (0–100)."""
    if counts.total == 0:
        return 0
    done_pct = 100 * counts.done / counts.total
    overdue_pct = 100 * counts.overdue / counts.total
    return max(0, min(100, round(0.5 * done_pct + 0.5 * avg_progress - overdue_pct)))


def _row(
    key: str,
    label: str,
    std: c.StatusCounts,
    prj: c.StatusCounts,
    avg: float | None,
    *,
    sublabel: str | None = None,
    team_id: UUID | None = None,
    assignee_id: UUID | None = None,
) -> c.DashboardBreakdownRow:
    both = counting.add(std, prj)
    avg = float(avg or 0)  # Postgres avg() Decimal döner
    return c.DashboardBreakdownRow(
        id=key,
        label=label,
        sublabel=sublabel,
        team_id=team_id,
        assignee_id=assignee_id,
        all=both,
        standard=std,
        project=prj,
        avg_progress=round(avg or 0),
        score=score(both, avg or 0),
    )


def _grouped(
    db: Session, key: Any, where: list[Any]
) -> tuple[dict[tuple[Any, ...], c.StatusCounts], dict[Any, float]]:
    by = counting.counts_by(db, [key, Task.type], where)
    avg = dict(
        db.execute(  # type: ignore[arg-type]
            select(key, func.avg(Task.progress)).where(counting.live_task_filter(), *where).group_by(key)
        ).all()
    )
    return by, avg


def _split(by: dict[tuple[Any, ...], c.StatusCounts], k: Any) -> tuple[c.StatusCounts, c.StatusCounts]:
    return by.get((k, TaskType.STANDARD), counting.empty()), by.get((k, TaskType.PROJECT), counting.empty())


def breakdown(db: Session, user: User, scope: set[UUID] | None, where: list[Any]) -> c.DashboardBreakdown:
    kind = KIND_BY_ROLE.get(user.role, BK.NONE)
    rows: list[c.DashboardBreakdownRow] = []
    if kind == BK.MEMBER:
        managed = managed_team_ids(db, user) or set()
        if scope is not None:
            managed &= scope
        members = list(
            db.scalars(
                select(User)
                .where(User.team_id.in_(managed), User.is_active.is_(True), User.id != user.id)
                .order_by(User.full_name)
            ).unique()
        )
        by, avg = _grouped(db, Task.assignee_id, [*where, Task.team_id.in_(managed)])
        for m in members:
            std, prj = _split(by, m.id)
            rows.append(
                _row(
                    str(m.id),
                    m.full_name,
                    std,
                    prj,
                    avg.get(m.id),
                    sublabel=m.team.name if m.team else None,
                    team_id=m.team_id,
                    assignee_id=m.id,
                )
            )
    elif kind == BK.TEAM_MANAGER:
        managed = managed_team_ids(db, user) or set()
        if scope is not None:
            managed &= scope
        teams = list(db.scalars(select(Team).where(Team.id.in_(managed)).order_by(Team.name)).unique())
        by, avg = _grouped(db, Task.team_id, where)
        for t in teams:
            std, prj = _split(by, t.id)
            label = t.manager.full_name if t.manager else "Ekip yöneticisi atanmamış"
            rows.append(_row(str(t.id), label, std, prj, avg.get(t.id), sublabel=t.name, team_id=t.id))
        rows.sort(key=lambda r: (-r.score, r.label))
    elif kind == BK.UNIT:
        unit_of = select(Team.unit_id).where(Team.id == Task.team_id).scalar_subquery()
        by, avg = _grouped(db, unit_of, where)
        units = list(db.scalars(select(Unit).order_by(Unit.name)).unique())
        for u in units:
            std, prj = _split(by, u.id)
            sub = f"{u.description} · {u.manager.full_name}" if u.manager else u.description
            rows.append(_row(str(u.id), u.name, std, prj, avg.get(u.id), sublabel=sub))
        std, prj = _split(by, None)
        if counting.add(std, prj).total:
            rows.append(_row("none", "Unit'e bağlı olmayan ekipler", std, prj, avg.get(None)))
    return c.DashboardBreakdown(kind=kind, rows=rows)


def today_counts(db: Session, user: User, scope: set[UUID] | None) -> c.DashboardToday:
    """Son tarihi bugün olan task'lar: çalışan için kendi (sorumlu/yedek), diğer roller için kapsamı."""
    today = date.today()
    who = (
        (Task.assignee_id == user.id) | (Task.backup_assignee_id == user.id)
        if user.role == Role.EMPLOYEE
        else team_filter(Task.team_id, scope)
    )
    mine = [counting.live_task_filter(), Task.due_date == today, who]
    total = db.scalar(select(func.count()).select_from(Task).where(*mine)) or 0
    done = db.scalar(select(func.count()).select_from(Task).where(*mine, Task.status == TaskStatus.DONE)) or 0
    return c.DashboardToday(total=total, done=done)


def approvals(db: Session, user: User) -> c.DashboardApprovals:
    """Karar verebilen için kararını bekleyen talepler; diğerleri için kendi talepleri."""
    since = utcnow() - timedelta(days=30)
    if user.role == Role.DIRECTOR:
        whose = None
    elif user.role in (Role.MANAGER, Role.UNIT_MANAGER):
        teams = managed_team_ids(db, user) or set()
        whose = EventParticipation.user_id.in_(
            select(User.id).where(User.team_id.in_(teams), User.id != user.id)
        )
    else:
        whose = EventParticipation.user_id == user.id
    base = [whose] if whose is not None else []
    pending = db.scalar(
        select(func.count())
        .select_from(EventParticipation)
        .where(*base, EventParticipation.status == ParticipationStatus.REQUESTED)
    )
    decided = db.scalar(
        select(func.count())
        .select_from(EventParticipation)
        .where(*base, EventParticipation.decided_at >= since)
    )
    return c.DashboardApprovals(pending=pending or 0, decided=decided or 0)


def missing_backup(db: Session, user: User) -> int:
    if user.role not in (Role.MANAGER, Role.UNIT_MANAGER, Role.DIRECTOR):
        return 0
    managed = managed_team_ids(db, user)
    return (
        db.scalar(
            select(func.count())
            .select_from(Task)
            .where(
                counting.live_task_filter(),
                team_filter(Task.team_id, managed),
                Task.status != TaskStatus.DONE,
                Task.backup_assignee_id.is_(None),
            )
        )
        or 0
    )


def summary(
    db: Session, user: User, team_id: UUID | None, frm: date | None, to: date | None
) -> c.DashboardSummary:
    scope = visible_team_ids(db, user)
    if team_id is not None:
        if not in_scope(team_id, scope):
            raise NotFound("Ekip bulunamadı.")
        scope = {team_id}
    where = [team_filter(Task.team_id, scope)]
    if frm:
        where.append(Task.created_at >= frm)
    if to:
        where.append(Task.created_at < to + timedelta(days=1))

    by = counting.counts_by(db, [Task.team_id, Task.type], where)
    avg_by_team = dict(
        db.execute(  # type: ignore[arg-type]
            select(Task.team_id, func.avg(Task.progress))
            .where(counting.live_task_filter(), *where)
            .group_by(Task.team_id)
        ).all()
    )
    overall = db.scalar(select(func.avg(Task.progress)).where(counting.live_task_filter(), *where))
    mine_avg = db.scalar(
        select(func.avg(Task.progress)).where(
            counting.live_task_filter(), *where[1:], involved_filter(user.id)
        )
    )
    teams = list(db.scalars(select(Team).where(team_filter(Team.id, scope)).order_by(Team.name)).unique())
    team_rows: list[c.TeamDashboard] = []
    tot_std, tot_prj = counting.empty(), counting.empty()
    for t in teams:
        std = by.get((t.id, TaskType.STANDARD), counting.empty())
        prj = by.get((t.id, TaskType.PROJECT), counting.empty())
        tot_std, tot_prj = counting.add(tot_std, std), counting.add(tot_prj, prj)
        team_rows.append(
            c.TeamDashboard(
                team_id=t.id,
                team_name=t.name,
                all=counting.add(std, prj),
                standard=std,
                project=prj,
                avg_progress=round(avg_by_team.get(t.id) or 0),
            )
        )
    mine = counting.counts(db, [*where, Task.assignee_id == user.id])
    watching = list(
        db.scalars(
            select(Task)
            .join(TaskWatcher, TaskWatcher.task_id == Task.id)
            .where(TaskWatcher.user_id == user.id, Task.deleted_at.is_(None))
            .order_by(Task.updated_at.desc())
            .limit(10)
        ).unique()
    )

    projects = list(
        db.scalars(
            select(Project)
            .where(
                Project.deleted_at.is_(None),
                Project.status == ProjectStatus.ACTIVE,
                team_filter(Project.team_id, scope),
            )
            .order_by(Project.due_date.asc().nulls_last(), Project.name)
            .limit(10)
        ).unique()
    )
    prog = progress_for(db, [p.id for p in projects])
    return c.DashboardSummary(
        generated_at=utcnow(),
        totals=c.TeamDashboardTotals(all=counting.add(tot_std, tot_prj), standard=tot_std, project=tot_prj),
        breakdown=breakdown(db, user, scope, where),
        today=today_counts(db, user, scope),
        approvals=approvals(db, user),
        missing_backup=missing_backup(db, user),
        teams=team_rows,
        mine=mine,
        avg_progress=round(overall or 0),
        mine_avg_progress=round(mine_avg or 0),
        watching=[
            c.WatchingItem(
                id=t.id, title=t.title, status=t.status, progress=t.progress, updated_at=t.updated_at
            )
            for t in watching
        ],
        projects=[
            c.Project2(
                id=p.id,
                name=p.name,
                team_id=p.team_id,
                due_date=p.due_date,
                progress=prog.get(p.id, counting.empty()),
            )
            for p in projects
        ],
    )
