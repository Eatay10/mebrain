"""Worker süreci: `python -m app.worker`. Zamanlamalar ADR-0004."""

from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.logging import configure_logging, log
from app.worker.jobs import run


def main() -> None:
    configure_logging("worker")
    sched = BlockingScheduler(timezone="Europe/Istanbul", job_defaults={"coalesce": True, "max_instances": 1})
    sched.add_job(run, "cron", args=["generate_recurring_tasks"], hour=0, minute=5)
    sched.add_job(run, "cron", args=["due_soon_notifications"], minute=0)
    sched.add_job(run, "cron", args=["overdue_notifications"], hour=9, minute=0)
    sched.add_job(run, "interval", args=["send_email_notifications"], minutes=1)
    sched.add_job(run, "interval", args=["cleanup_sessions"], hours=1)
    sched.add_job(run, "interval", args=["run_report_schedules"], minutes=5)
    # Başlangıçta bir kez: kapalı kalınan süreyi telafi eder (idempotent).
    for name in (
        "generate_recurring_tasks",
        "due_soon_notifications",
        "overdue_notifications",
        "run_report_schedules",
    ):
        run(name)
    log.info("worker_started")
    sched.start()


if __name__ == "__main__":
    main()
