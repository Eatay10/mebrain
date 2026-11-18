# GENERATED from openapi.yaml by scripts/gen_contract.sh — do not edit.

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import AnyUrl, AwareDatetime, BaseModel, ConfigDict, EmailStr, Field
from typing_extensions import TypeAliasType


class Role(StrEnum):
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"
    DIRECTOR = "DIRECTOR"
    AUDITOR = "AUDITOR"


class TaskType(StrEnum):
    STANDARD = "STANDARD"
    PROJECT = "PROJECT"


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    DONE = "DONE"


class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskCategory(StrEnum):
    INCIDENT_RESPONSE = "INCIDENT_RESPONSE"
    VULNERABILITY_MANAGEMENT = "VULNERABILITY_MANAGEMENT"
    MONITORING = "MONITORING"
    PENETRATION_TEST = "PENETRATION_TEST"
    COMPLIANCE = "COMPLIANCE"
    THREAT_INTEL = "THREAT_INTEL"
    AWARENESS = "AWARENESS"
    OPERATIONS = "OPERATIONS"
    OTHER = "OTHER"


class Recurrence(StrEnum):
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class ProjectStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class EventType(StrEnum):
    CONFERENCE = "CONFERENCE"
    TRAINING = "TRAINING"
    CTF = "CTF"
    WEBINAR = "WEBINAR"
    WORKSHOP = "WORKSHOP"
    MEETUP = "MEETUP"
    OTHER = "OTHER"


class EventScope(StrEnum):
    INDIVIDUAL = "INDIVIDUAL"
    CORPORATE = "CORPORATE"


class ParticipationRole(StrEnum):
    ATTENDEE = "ATTENDEE"
    SPEAKER = "SPEAKER"
    ORGANIZER = "ORGANIZER"
    INSTRUCTOR = "INSTRUCTOR"


class ParticipationStatus(StrEnum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ATTENDED = "ATTENDED"
    CANCELLED = "CANCELLED"


class CompetencyCategory(StrEnum):
    OFFENSIVE = "OFFENSIVE"
    DEFENSIVE = "DEFENSIVE"
    GRC = "GRC"
    CLOUD = "CLOUD"
    APPSEC = "APPSEC"
    FORENSICS = "FORENSICS"
    NETWORK = "NETWORK"
    OTHER = "OTHER"


class NotificationType(StrEnum):
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_BACKUP_ASSIGNED = "TASK_BACKUP_ASSIGNED"
    TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED"
    TASK_COMMENTED = "TASK_COMMENTED"
    TASK_DUE_SOON = "TASK_DUE_SOON"
    TASK_OVERDUE = "TASK_OVERDUE"
    PARTICIPATION_DECIDED = "PARTICIPATION_DECIDED"
    ANNOUNCEMENT = "ANNOUNCEMENT"


class ApiScope(StrEnum):
    TASKS_READ = "tasks:read"
    TASKS_WRITE = "tasks:write"
    PROJECTS_READ = "projects:read"
    REPORTS_READ = "reports:read"
    EVENTS_READ = "events:read"
    EVENTS_WRITE = "events:write"
    COMPETENCIES_READ = "competencies:read"


class SecurityEventType(StrEnum):
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    LOGOUT = "LOGOUT"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    CSRF_REJECTED = "CSRF_REJECTED"
    AUTHZ_DENIED = "AUTHZ_DENIED"
    NOT_FOUND_PROBE = "NOT_FOUND_PROBE"
    VALIDATION_REJECTED = "VALIDATION_REJECTED"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    RATE_LIMITED = "RATE_LIMITED"
    ROLE_CHANGED = "ROLE_CHANGED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    API_TOKEN_CREATED = "API_TOKEN_CREATED"
    API_TOKEN_REVOKED = "API_TOKEN_REVOKED"
    API_TOKEN_INVALID = "API_TOKEN_INVALID"
    BULK_EXPORT = "BULK_EXPORT"


class SecuritySeverity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Error(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    field: str
    message: str


class Problem(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    type: str
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    request_id: Annotated[str | None, Field(alias="requestId")] = None
    errors: list[Error] | None = None


class PageMeta(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    total: Annotated[int, Field(ge=0)]
    page: Annotated[int, Field(ge=1)]
    page_size: Annotated[int, Field(alias="pageSize", ge=1)]


class Status(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


class HealthStatus(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    status: Status
    checks: dict[str, str] | None = None
    version: str | None = None


class UserRef(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    full_name: Annotated[str, Field(alias="fullName")]


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    email: Annotated[EmailStr, Field(max_length=254)]
    password: Annotated[str, Field(max_length=128, min_length=1)]


class ApiToken(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    name: str
    prefix: str
    scopes: list[ApiScope]
    created_at: Annotated[AwareDatetime, Field(alias="createdAt")]
    expires_at: Annotated[AwareDatetime, Field(alias="expiresAt")]
    last_used_at: Annotated[AwareDatetime | None, Field(alias="lastUsedAt")] = None
    revoked_at: Annotated[AwareDatetime | None, Field(alias="revokedAt")] = None


class ApiTokenCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    name: Annotated[str, Field(max_length=100, min_length=1)]
    scopes: Annotated[list[ApiScope], Field(min_length=1)]
    expires_in_days: Annotated[
        int | None, Field(alias="expiresInDays", ge=1, le=90)
    ] = 30


class ApiTokenCreated(ApiToken):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    token: Annotated[
        str, Field(description="Düz metin token — yalnızca bu yanıtta döner")
    ]


class User(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    email: EmailStr
    full_name: Annotated[str, Field(alias="fullName")]
    title: str | None = None
    role: Role
    team_id: Annotated[UUID | None, Field(alias="teamId")] = None
    team_name: Annotated[str | None, Field(alias="teamName")] = None
    is_active: Annotated[bool, Field(alias="isActive")]
    last_login_at: Annotated[AwareDatetime | None, Field(alias="lastLoginAt")] = None


class UserPage(PageMeta):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    items: list[User]


class UserCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    email: Annotated[EmailStr, Field(max_length=254)]
    full_name: Annotated[str, Field(alias="fullName", max_length=120, min_length=2)]
    title: Annotated[str | None, Field(max_length=120)] = None
    role: Role
    team_id: Annotated[UUID | None, Field(alias="teamId")] = None
    password: Annotated[str, Field(max_length=128, min_length=12)]


class UserUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    full_name: Annotated[
        str | None, Field(alias="fullName", max_length=120, min_length=2)
    ] = None
    title: Annotated[str | None, Field(max_length=120)] = None
    role: Role | None = None
    team_id: Annotated[UUID | None, Field(alias="teamId")] = None
    is_active: Annotated[bool | None, Field(alias="isActive")] = None


class Team(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    name: str
    description: str | None = None
    manager: UserRef | None = None
    member_count: Annotated[int, Field(alias="memberCount", ge=0)]


class TeamCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    name: Annotated[str, Field(max_length=100, min_length=2)]
    description: Annotated[str | None, Field(max_length=1000)] = None
    manager_id: Annotated[UUID | None, Field(alias="managerId")] = None


class TeamUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    name: Annotated[str | None, Field(max_length=100, min_length=2)] = None
    description: Annotated[str | None, Field(max_length=1000)] = None
    manager_id: Annotated[UUID | None, Field(alias="managerId")] = None


class ProjectCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    team_id: Annotated[UUID, Field(alias="teamId")]
    name: Annotated[str, Field(max_length=150, min_length=2)]
    description: Annotated[str | None, Field(max_length=10000)] = None
    owner_id: Annotated[UUID | None, Field(alias="ownerId")] = None
    start_date: Annotated[date | None, Field(alias="startDate")] = None
    due_date: Annotated[date | None, Field(alias="dueDate")] = None


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    name: Annotated[str | None, Field(max_length=150, min_length=2)] = None
    description: Annotated[str | None, Field(max_length=10000)] = None
    owner_id: Annotated[UUID | None, Field(alias="ownerId")] = None
    status: ProjectStatus | None = None
    start_date: Annotated[date | None, Field(alias="startDate")] = None
    due_date: Annotated[date | None, Field(alias="dueDate")] = None


class Project1(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    name: str


class Task(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    type: TaskType
    team_id: Annotated[UUID, Field(alias="teamId")]
    team_name: Annotated[str | None, Field(alias="teamName")] = None
    project: Project1 | None = None
    title: str
    description: str | None = None
    status: TaskStatus
    blocked_reason: Annotated[str | None, Field(alias="blockedReason")] = None
    priority: TaskPriority
    category: TaskCategory
    assignee: UserRef | None = None
    backup_assignee: Annotated[UserRef | None, Field(alias="backupAssignee")] = None
    due_date: Annotated[date | None, Field(alias="dueDate")] = None
    is_overdue: Annotated[bool, Field(alias="isOverdue")]
    recurrence: Recurrence
    recurrence_parent_id: Annotated[UUID | None, Field(alias="recurrenceParentId")] = (
        None
    )
    started_at: Annotated[AwareDatetime | None, Field(alias="startedAt")] = None
    completed_at: Annotated[AwareDatetime | None, Field(alias="completedAt")] = None
    created_by: Annotated[UserRef | None, Field(alias="createdBy")] = None
    comment_count: Annotated[int | None, Field(alias="commentCount", ge=0)] = None
    version: Annotated[int, Field(ge=1)]
    created_at: Annotated[AwareDatetime, Field(alias="createdAt")]
    updated_at: Annotated[AwareDatetime, Field(alias="updatedAt")]


class TaskPage(PageMeta):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    items: list[Task]


class TaskCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    type: TaskType
    team_id: Annotated[UUID | None, Field(alias="teamId")] = None
    project_id: Annotated[UUID | None, Field(alias="projectId")] = None
    title: Annotated[str, Field(max_length=200, min_length=3)]
    description: Annotated[str | None, Field(max_length=10000)] = None
    priority: TaskPriority | None = None
    category: TaskCategory | None = None
    assignee_id: Annotated[UUID | None, Field(alias="assigneeId")] = None
    backup_assignee_id: Annotated[UUID | None, Field(alias="backupAssigneeId")] = None
    due_date: Annotated[date | None, Field(alias="dueDate")] = None
    recurrence: Recurrence | None = None


class TaskUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    version: Annotated[
        int, Field(description="Optimistic locking; uyuşmazsa 409", ge=1)
    ]
    title: Annotated[str | None, Field(max_length=200, min_length=3)] = None
    description: Annotated[str | None, Field(max_length=10000)] = None
    priority: TaskPriority | None = None
    category: TaskCategory | None = None
    assignee_id: Annotated[UUID | None, Field(alias="assigneeId")] = None
    backup_assignee_id: Annotated[UUID | None, Field(alias="backupAssigneeId")] = None
    due_date: Annotated[date | None, Field(alias="dueDate")] = None
    recurrence: Recurrence | None = None


class TaskTransition(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    to: TaskStatus
    version: Annotated[int, Field(ge=1)]
    reason: Annotated[
        str | None, Field(description="to=BLOCKED ise zorunlu", max_length=500)
    ] = None


class Comment(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    task_id: Annotated[UUID, Field(alias="taskId")]
    author: UserRef
    body: str
    created_at: Annotated[AwareDatetime, Field(alias="createdAt")]


class CommentPage(PageMeta):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    items: list[Comment]


class CommentCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    body: Annotated[str, Field(max_length=5000, min_length=1)]


class StatusCounts(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    todo: Annotated[int, Field(description="Başlanmadı", ge=0)]
    in_progress: Annotated[
        int, Field(alias="inProgress", description="Devam ediyor", ge=0)
    ]
    blocked: Annotated[int, Field(description="Bloklu", ge=0)]
    done: Annotated[int, Field(description="Tamamlandı", ge=0)]
    overdue: Annotated[
        int,
        Field(
            description="Son tarihi geçmiş ve tamamlanmamış (diğer sayılarla kesişir)",
            ge=0,
        ),
    ]
    total: Annotated[int, Field(ge=0)]


class TeamDashboard(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    team_id: Annotated[UUID, Field(alias="teamId")]
    team_name: Annotated[str, Field(alias="teamName")]
    all: StatusCounts
    standard: StatusCounts
    project: StatusCounts


class Project2(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    name: str
    team_id: Annotated[UUID, Field(alias="teamId")]
    due_date: Annotated[date | None, Field(alias="dueDate")] = None
    progress: StatusCounts


class TeamDashboardTotals(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    all: StatusCounts
    standard: StatusCounts
    project: StatusCounts


class Row(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    key: str
    label: str
    counts: StatusCounts
    avg_completion_hours: Annotated[float | None, Field(alias="avgCompletionHours")] = (
        None
    )


class TaskReport(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    group_by: Annotated[str, Field(alias="groupBy")]
    from_: Annotated[date, Field(alias="from")]
    to: date
    rows: list[Row]
    totals: StatusCounts


class Notification(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    type: NotificationType
    title: str
    body: str | None = None
    entity_type: Annotated[str | None, Field(alias="entityType")] = None
    entity_id: Annotated[UUID | None, Field(alias="entityId")] = None
    read_at: Annotated[AwareDatetime | None, Field(alias="readAt")] = None
    created_at: Annotated[AwareDatetime, Field(alias="createdAt")]


class NotificationPage(PageMeta):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    items: list[Notification]


class Scope(StrEnum):
    TEAM = "TEAM"
    ORGANIZATION = "ORGANIZATION"


class Announcement(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    scope: Scope
    team_id: Annotated[UUID | None, Field(alias="teamId")] = None
    title: str
    body: str
    author: UserRef
    pinned: bool
    created_at: Annotated[AwareDatetime, Field(alias="createdAt")]


class AnnouncementPage(PageMeta):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    items: list[Announcement]


class AnnouncementCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    scope: Scope
    team_id: Annotated[UUID | None, Field(alias="teamId")] = None
    title: Annotated[str, Field(max_length=200, min_length=3)]
    body: Annotated[str, Field(max_length=5000, min_length=1)]
    pinned: bool | None = False


class EventCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    title: Annotated[str, Field(max_length=200, min_length=3)]
    type: EventType
    scope: EventScope
    description: Annotated[str | None, Field(max_length=10000)] = None
    organizer: Annotated[str | None, Field(max_length=150)] = None
    location: Annotated[str | None, Field(max_length=200)] = None
    url: AnyUrl | None = None
    starts_at: Annotated[AwareDatetime, Field(alias="startsAt")]
    ends_at: Annotated[AwareDatetime, Field(alias="endsAt")]


class EventUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    title: Annotated[str | None, Field(max_length=200, min_length=3)] = None
    type: EventType | None = None
    description: Annotated[str | None, Field(max_length=10000)] = None
    organizer: Annotated[str | None, Field(max_length=150)] = None
    location: Annotated[str | None, Field(max_length=200)] = None
    url: AnyUrl | None = None
    starts_at: Annotated[AwareDatetime | None, Field(alias="startsAt")] = None
    ends_at: Annotated[AwareDatetime | None, Field(alias="endsAt")] = None


class Participation(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    event_id: Annotated[UUID, Field(alias="eventId")]
    user: UserRef
    role: ParticipationRole
    status: ParticipationStatus
    decided_by: Annotated[UserRef | None, Field(alias="decidedBy")] = None
    decided_at: Annotated[AwareDatetime | None, Field(alias="decidedAt")] = None
    note: str | None = None
    created_at: Annotated[AwareDatetime, Field(alias="createdAt")]


class ParticipationCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    user_id: Annotated[
        UUID | None, Field(alias="userId", description="Boşsa oturumdaki kullanıcı")
    ] = None
    role: ParticipationRole
    note: Annotated[str | None, Field(max_length=500)] = None


class Status1(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ATTENDED = "ATTENDED"
    CANCELLED = "CANCELLED"


class ParticipationDecision(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    status: Status1
    note: Annotated[str | None, Field(max_length=500)] = None


class Competency(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    name: str
    category: CompetencyCategory
    description: str | None = None


class CompetencyCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    name: Annotated[str, Field(max_length=100, min_length=2)]
    category: CompetencyCategory
    description: Annotated[str | None, Field(max_length=1000)] = None


class UserCompetency(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    user_id: Annotated[UUID, Field(alias="userId")]
    competency: Competency
    level: Annotated[int, Field(ge=1, le=5)]
    evidence: str | None = None
    verified_by: Annotated[UserRef | None, Field(alias="verifiedBy")] = None
    verified_at: Annotated[AwareDatetime | None, Field(alias="verifiedAt")] = None
    updated_at: Annotated[AwareDatetime, Field(alias="updatedAt")]


class UserCompetencyUpsert(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    level: Annotated[int, Field(ge=1, le=5)]
    evidence: Annotated[str | None, Field(max_length=500)] = None
    verified: Annotated[
        bool | None,
        Field(description="Sadece yönetici+ set edebilir; çalışan gönderirse 403"),
    ] = None


LevelsAdditionalProperty = TypeAliasType(
    "LevelsAdditionalProperty", Annotated[int, Field(ge=1, le=5)]
)


class Member(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    user: UserRef
    levels: Annotated[
        dict[str, LevelsAdditionalProperty],
        Field(description="competencyId → seviye (1–5)"),
    ]


class CompetencyMatrix(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    team_id: Annotated[UUID, Field(alias="teamId")]
    competencies: list[Competency]
    members: list[Member]


class ActorType(StrEnum):
    USER = "USER"
    API_TOKEN = "API_TOKEN"
    SYSTEM = "SYSTEM"


class Result(StrEnum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    FAILED = "FAILED"


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: int
    occurred_at: Annotated[AwareDatetime, Field(alias="occurredAt")]
    actor: UserRef | None = None
    actor_type: Annotated[ActorType, Field(alias="actorType")]
    action: str
    entity_type: Annotated[str | None, Field(alias="entityType")] = None
    entity_id: Annotated[UUID | None, Field(alias="entityId")] = None
    changes: dict[str, Any] | None = None
    ip: str | None = None
    request_id: Annotated[str | None, Field(alias="requestId")] = None
    result: Result


class AuditLogPage(PageMeta):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    items: list[AuditLogEntry]


class SecurityEvent(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: int
    occurred_at: Annotated[AwareDatetime, Field(alias="occurredAt")]
    type: SecurityEventType
    severity: SecuritySeverity
    user: UserRef | None = None
    ip: str | None = None
    request_id: Annotated[str | None, Field(alias="requestId")] = None
    details: dict[str, Any] | None = None


class SecurityEventPage(PageMeta):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    items: list[SecurityEvent]


class TimelineItem(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    bucket: AwareDatetime
    count: int
    by_type: Annotated[dict[str, int] | None, Field(alias="byType")] = None


class TopSource(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    ip: str
    count: int
    last_seen: Annotated[AwareDatetime | None, Field(alias="lastSeen")] = None


class OpenAlert(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    rule: str
    severity: SecuritySeverity
    first_seen: Annotated[AwareDatetime, Field(alias="firstSeen")]
    count: int
    sample: str | None = None


class SecuritySummary(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    window: str
    counts_by_type: Annotated[dict[str, int], Field(alias="countsByType")]
    timeline: list[TimelineItem]
    top_sources: Annotated[list[TopSource], Field(alias="topSources")]
    open_alerts: Annotated[list[OpenAlert], Field(alias="openAlerts")]


class Endpoint(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    route: str
    method: str
    requests: int
    error_rate: Annotated[float, Field(alias="errorRate", ge=0.0, le=1.0)]
    p50_ms: Annotated[float, Field(alias="p50Ms")]
    p95_ms: Annotated[float, Field(alias="p95Ms")]
    p99_ms: Annotated[float, Field(alias="p99Ms")]


class LastStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    NEVER_RAN = "NEVER_RAN"


class Job(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    name: str
    last_run_at: Annotated[AwareDatetime | None, Field(alias="lastRunAt")]
    last_status: Annotated[LastStatus, Field(alias="lastStatus")]
    last_duration_ms: Annotated[int | None, Field(alias="lastDurationMs")] = None


class MetricsSummary(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    window: str
    uptime_seconds: Annotated[int | None, Field(alias="uptimeSeconds")] = None
    endpoints: list[Endpoint]
    jobs: list[Job]


class Session(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    user: User
    csrf_token: Annotated[str, Field(alias="csrfToken")]
    visible_team_ids: Annotated[list[UUID], Field(alias="visibleTeamIds")]
    managed_team_ids: Annotated[list[UUID] | None, Field(alias="managedTeamIds")] = None
    expires_at: Annotated[AwareDatetime | None, Field(alias="expiresAt")] = None


class Project(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    team_id: Annotated[UUID, Field(alias="teamId")]
    team_name: Annotated[str | None, Field(alias="teamName")] = None
    name: str
    description: str | None = None
    owner: UserRef | None = None
    status: ProjectStatus
    start_date: Annotated[date | None, Field(alias="startDate")] = None
    due_date: Annotated[date | None, Field(alias="dueDate")] = None
    progress: StatusCounts
    created_at: Annotated[AwareDatetime, Field(alias="createdAt")]


class ProjectPage(PageMeta):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    items: list[Project]


class DashboardSummary(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    generated_at: Annotated[AwareDatetime, Field(alias="generatedAt")]
    totals: TeamDashboardTotals
    teams: list[TeamDashboard]
    mine: StatusCounts
    projects: Annotated[
        list[Project2],
        Field(
            description="Kapsamdaki aktif projelerin ilerlemesi (en fazla 10, son tarihe göre)"
        ),
    ]


class Event(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    id: UUID
    title: str
    type: EventType
    scope: EventScope
    description: str | None = None
    organizer: str | None = None
    location: str | None = None
    url: AnyUrl | None = None
    starts_at: Annotated[AwareDatetime, Field(alias="startsAt")]
    ends_at: Annotated[AwareDatetime, Field(alias="endsAt")]
    created_by: Annotated[UserRef, Field(alias="createdBy")]
    participant_count: Annotated[int | None, Field(alias="participantCount", ge=0)] = (
        None
    )
    my_participation: Annotated[
        Participation | None, Field(alias="myParticipation")
    ] = None


class EventPage(PageMeta):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    items: list[Event]
