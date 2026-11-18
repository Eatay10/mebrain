"""Dashboard özeti — ekip × tür durum sayıları (DSH-01..03)."""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.scope import in_scope, team_filter, visible_team_ids
from app.contract import ProjectStatus, TaskType
from app.core.errors import NotFound
from app.models import Project, Task, Team, User
from app.models.base import utcnow
from app.modules.projects.service import progress_for
from app.modules.tasks import counting


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
    teams = list(db.scalars(select(Team).where(team_filter(Team.id, scope)).order_by(Team.name)).unique())
    team_rows: list[c.TeamDashboard] = []
    tot_std, tot_prj = counting.empty(), counting.empty()
    for t in teams:
        std = by.get((t.id, TaskType.STANDARD), counting.empty())
        prj = by.get((t.id, TaskType.PROJECT), counting.empty())
        tot_std, tot_prj = counting.add(tot_std, std), counting.add(tot_prj, prj)
        team_rows.append(
            c.TeamDashboard(
                team_id=t.id, team_name=t.name, all=counting.add(std, prj), standard=std, project=prj
            )
        )
    mine = counting.counts(db, [*where, Task.assignee_id == user.id])

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
        teams=team_rows,
        mine=mine,
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
