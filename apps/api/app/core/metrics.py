"""Prometheus metrikleri + uygulama içi RED özeti için kısa süreli örnek deposu."""

import threading
import time
from collections import deque
from dataclasses import dataclass

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter("http_requests_total", "HTTP istekleri", ["method", "route", "status"])
HTTP_DURATION = Histogram("http_request_duration_seconds", "HTTP süreleri", ["method", "route"])
SECURITY_EVENTS = Counter("security_events_total", "Güvenlik olayları", ["type", "severity"])
AUTH_LOGINS = Counter("auth_logins_total", "Giriş denemeleri", ["result"])
TASK_TRANSITIONS = Counter("tasks_transitions_total", "Task durum geçişleri", ["from_status", "to_status"])
NOTIFICATIONS_SENT = Counter("notifications_sent_total", "Bildirimler", ["channel", "result"])
JOB_RUNS = Counter("job_runs_total", "Worker işleri", ["job", "result"])
JOB_DURATION = Histogram("job_duration_seconds", "Worker iş süreleri", ["job"])
DB_POOL_IN_USE = Gauge("db_pool_in_use", "Kullanımdaki DB bağlantıları")

STARTED_AT = time.time()


@dataclass(frozen=True)
class Sample:
    ts: float
    method: str
    route: str
    status: int
    duration_ms: float


class RecentSamples:
    """Son 24 saatin istek örnekleri (en fazla 200k) — /system/metrics-summary için."""

    def __init__(self, maxlen: int = 200_000) -> None:
        self._q: deque[Sample] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def add(self, s: Sample) -> None:
        with self._lock:
            self._q.append(s)

    def since(self, seconds: float) -> list[Sample]:
        cutoff = time.time() - seconds
        with self._lock:
            return [s for s in self._q if s.ts >= cutoff]


recent = RecentSamples()


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, round(p / 100 * (len(ordered) - 1))))
    return round(ordered[k], 2)
