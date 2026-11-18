"""Zamanlanmış işler (ADR-0004). Hepsi idempotent; sistem aktörüyle audit yazar."""

import calendar
import time
from collections.abc import Callable
from datetime import date, timedelta

from sqlalchemy import delete, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.audit.service import record
from app.contract import NotificationType as NT
from app.contract import Recurrence, TaskStatus
from app.core import context, metrics
from app.core.logging import log
from app.db import SessionLocal
from app.email.sender import send
from app.models import JobRun, Notification, Task, UserSession
from app.models.base import utcnow
from app.modules.notifications.service import notify

MAX_BACKFILL_DAYS = 7


def occurrences(tpl: Task, start: date, end: date) -> list[date]:
    """knowledge/domain/recurrence.md: DAILY iş günleri, WEEKLY oluşturulduğu gün, MONTHLY ayın aynı günü."""
    out, d = [], start
    anchor = tpl.created_at.date()
    while d <= end:
        daily = tpl.recurrence == Recurrence.DAILY and d.weekday() < 5
        weekly = tpl.recurrence == Recurrence.WEEKLY and d.weekday() == anchor.weekday()
        last = calendar.monthrange(d.year, d.month)[1]
        monthly = tpl.recurrence == Recurrence.MONTHLY and d.day == min(anchor.day, last)
        if daily or weekly or monthly:
            out.append(d)
        d += timedelta(days=1)
    return out


def generate_recurring_tasks(db: Session, today: date | None = None) -> int:
    today = today or date.today()
    created = 0
    templates = db.scalars(
        select(Task).where(Task.recurrence != Recurrence.NONE, Task.deleted_at.is_(None))
    ).unique()
    for tpl in templates:
        start = max(today - timedelta(days=MAX_BACKFILL_DAYS), tpl.created_at.date())
        assignee = tpl.assignee if tpl.assignee and tpl.assignee.is_active else None
        backup = tpl.backup_assignee if tpl.backup_assignee and tpl.backup_assignee.is_active else None
        if assignee is None and backup is not None:
            assignee, backup = backup, None
        for d in occurrences(tpl, start, today):
            res = db.execute(
                insert(Task)
                .values(
                    type=tpl.type,
                    team_id=tpl.team_id,
                    project_id=tpl.project_id,
                    title=tpl.title,
                    description=tpl.description,
                    priority=tpl.priority,
                    category=tpl.category,
                    assignee_id=assignee.id if assignee else None,
                    backup_assignee_id=backup.id if backup else None,
                    due_date=d,
                    recurrence=Recurrence.NONE,
                    recurrence_parent_id=tpl.id,
                    occurrence_date=d,
                    created_by=None,
                    status=TaskStatus.TODO,
                    version=1,
                )
                .on_conflict_do_nothing(constraint="uq_tasks_occurrence")
                .returning(Task.id)
            )
            new_id = res.scalar()
            if new_id is None:
                continue
            created += 1
            record(db, "task.create", "task", new_id, {"recurrenceParentId": [None, str(tpl.id)]})
            recipients = [assignee.id] if assignee else [tpl.team.manager_id]
            notify(
                db,
                recipients,
                NT.TASK_ASSIGNED,
                f"Rutin task: {tpl.title} ({d:%d.%m.%Y})",
                entity_type="task",
                entity_id=new_id,
                dedup_key=f"recurring:{new_id}",
            )
    return created


def due_soon_notifications(db: Session, today: date | None = None) -> int:
    today = today or date.today()
    tasks = db.scalars(
        select(Task).where(
            Task.deleted_at.is_(None),
            Task.recurrence == Recurrence.NONE,
            Task.status != TaskStatus.DONE,
            Task.due_date.in_([today, today + timedelta(days=1)]),
        )
    ).unique()
    n = 0
    for t in tasks:
        n += notify(
            db,
            [t.assignee_id, t.backup_assignee_id],
            NT.TASK_DUE_SOON,
            f"Son tarih yaklaşıyor: {t.title} ({t.due_date:%d.%m.%Y})",
            entity_type="task",
            entity_id=t.id,
            dedup_key=f"due_soon:{t.id}:{t.due_date}",
        )
    return n


def overdue_notifications(db: Session, today: date | None = None) -> int:
    today = today or date.today()
    tasks = db.scalars(
        select(Task).where(
            Task.deleted_at.is_(None),
            Task.recurrence == Recurrence.NONE,
            Task.status != TaskStatus.DONE,
            Task.due_date < today,
        )
    ).unique()
    n = 0
    for t in tasks:
        n += notify(
            db,
            [t.assignee_id, t.team.manager_id if t.team else None],
            NT.TASK_OVERDUE,
            f"Gecikmiş task: {t.title} (son tarih {t.due_date:%d.%m.%Y})",
            entity_type="task",
            entity_id=t.id,
            dedup_key=f"overdue:{t.id}:{today}",
        )
    return n


def send_email_notifications(db: Session, batch: int = 50) -> int:
    rows = list(
        db.scalars(
            select(Notification)
            .where(Notification.email_status == "PENDING")
            .order_by(Notification.created_at)
            .limit(batch)
            .with_for_update(skip_locked=True)
        ).unique()
    )
    sent = 0
    for n in rows:
        try:
            path = f"/{n.entity_type}s/{n.entity_id}" if n.entity_type and n.entity_id else None
            send(n.user.email, n.title, n.body or n.title, path)
            n.email_status = "SENT"
            sent += 1
            metrics.NOTIFICATIONS_SENT.labels("email", "sent").inc()
        except Exception as exc:
            n.email_attempts += 1
            n.email_status = "FAILED" if n.email_attempts >= 3 else "PENDING"
            metrics.NOTIFICATIONS_SENT.labels("email", "failed").inc()
            log.warning("email_failed", error_type=type(exc).__name__, attempts=n.email_attempts)
    return sent


def cleanup_sessions(db: Session) -> int:
    now = utcnow()
    res = db.execute(
        delete(UserSession).where(
            or_(UserSession.expires_at <= now, UserSession.last_seen_at <= now - timedelta(days=1))
        )
    )
    return res.rowcount or 0


def run_report_schedules(db: Session) -> int:
    from app.modules.reports.schedules import run_due

    return run_due(db)


JOBS: dict[str, Callable[[Session], int]] = {
    "run_report_schedules": run_report_schedules,
    "generate_recurring_tasks": generate_recurring_tasks,
    "due_soon_notifications": due_soon_notifications,
    "overdue_notifications": overdue_notifications,
    "send_email_notifications": send_email_notifications,
    "cleanup_sessions": cleanup_sessions,
}


def run(name: str) -> None:
    context.set_context(context.RequestContext(request_id=f"job-{name}", actor_type="SYSTEM"))
    started = time.perf_counter()
    status, processed, error = "SUCCESS", 0, None
    with SessionLocal() as db:
        try:
            processed = JOBS[name](db)
            db.commit()
        except Exception as exc:
            db.rollback()
            status, error = "FAILED", type(exc).__name__
            log.error("job_failed", job=name, error_type=error)
        duration = int((time.perf_counter() - started) * 1000)
        db.add(JobRun(job=name, duration_ms=duration, status=status, processed=processed, error=error))
        db.commit()
    metrics.JOB_RUNS.labels(name, status.lower()).inc()
    metrics.JOB_DURATION.labels(name).observe(duration / 1000)
    log.info("job_run", job=name, status=status, processed=processed, duration_ms=duration)


__all__ = ["JOBS", "occurrences", "run"]
