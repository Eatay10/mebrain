/**
 * Sunucu durumu yalnızca TanStack Query hook'larıyla (R-TS-02). Tüm çağrılar sözleşmeden üretilmiş
 * client üzerinden yapılır; sözleşmede olmayan uç noktaya erişim derleme hatasıdır.
 */
import { ApiError, createApi, unwrap, type paths, type Schemas } from "@cth/api-client";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export const api = createApi();
export type { Schemas };

type TaskQuery = NonNullable<paths["/tasks"]["get"]["parameters"]["query"]>;

export const qk = {
  me: ["me"] as const,
  dashboard: (p: object) => ["dashboard", p] as const,
  tasks: (p: object) => ["tasks", p] as const,
  task: (id: string) => ["task", id] as const,
};

// ---------------------------------------------------------------- auth
export function useMe() {
  return useQuery({
    queryKey: qk.me,
    queryFn: () => unwrap(api.GET("/auth/me")),
    retry: (count, err) => !(err instanceof ApiError && err.status === 401) && count < 2,
    staleTime: 60_000,
  });
}

export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["LoginRequest"]) => unwrap(api.POST("/auth/login", { body })),
    onSuccess: (session) => {
      qc.clear();
      qc.setQueryData(qk.me, session);
    },
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => unwrap(api.POST("/auth/logout", { params: { header: {} } })),
    onSettled: () => {
      qc.clear();
      qc.setQueryData(qk.me, null);
    },
  });
}

// ---------------------------------------------------------------- dashboard & reports
export function useDashboard(params: { teamId?: string }) {
  return useQuery({
    queryKey: qk.dashboard(params),
    queryFn: () => unwrap(api.GET("/dashboard/summary", { params: { query: params } })),
    refetchInterval: 60_000,
  });
}

export function useTaskReport(q: {
  groupBy: "team" | "assignee" | "project" | "status" | "priority" | "category" | "type";
  from: string;
  to: string;
  teamId?: string;
}) {
  return useQuery({
    queryKey: ["report", q],
    queryFn: () => unwrap(api.GET("/reports/tasks", { params: { query: q } })) as Promise<Schemas["TaskReport"]>,
  });
}

// ---------------------------------------------------------------- tasks
export type TaskFilters = Partial<TaskQuery>;

export function useTasks(filters: TaskFilters) {
  return useQuery({
    queryKey: qk.tasks(filters),
    queryFn: () => unwrap(api.GET("/tasks", { params: { query: filters } })),
    placeholderData: keepPreviousData,
  });
}

export function useTask(id: string | undefined) {
  return useQuery({
    queryKey: qk.task(id ?? ""),
    queryFn: () => unwrap(api.GET("/tasks/{taskId}", { params: { path: { taskId: id! } } })),
    enabled: !!id,
  });
}

function useInvalidateTasks() {
  const qc = useQueryClient();
  return () => {
    void qc.invalidateQueries({ queryKey: ["tasks"] });
    void qc.invalidateQueries({ queryKey: ["task"] });
    void qc.invalidateQueries({ queryKey: ["dashboard"] });
    void qc.invalidateQueries({ queryKey: ["projects"] });
    void qc.invalidateQueries({ queryKey: ["notifications"] });
  };
}

export function useCreateTask() {
  const done = useInvalidateTasks();
  return useMutation({
    mutationFn: (body: Schemas["TaskCreate"]) => unwrap(api.POST("/tasks", { body })),
    onSuccess: done,
  });
}

export function useUpdateTask(id: string) {
  const done = useInvalidateTasks();
  return useMutation({
    mutationFn: (body: Schemas["TaskUpdate"]) =>
      unwrap(api.PATCH("/tasks/{taskId}", { params: { path: { taskId: id } }, body })),
    onSuccess: done,
  });
}

export function useTransitionTask() {
  const done = useInvalidateTasks();
  return useMutation({
    mutationFn: ({ id, ...body }: Schemas["TaskTransition"] & { id: string }) =>
      unwrap(api.POST("/tasks/{taskId}/transitions", { params: { path: { taskId: id } }, body })),
    onSuccess: done,
  });
}

export function useDeleteTask() {
  const done = useInvalidateTasks();
  return useMutation({
    mutationFn: (id: string) => unwrap(api.DELETE("/tasks/{taskId}", { params: { path: { taskId: id } } })),
    onSuccess: done,
  });
}

export function useComments(taskId: string) {
  return useQuery({
    queryKey: ["comments", taskId],
    queryFn: () =>
      unwrap(api.GET("/tasks/{taskId}/comments", { params: { path: { taskId }, query: { pageSize: 100 } } })),
  });
}

export function useAddComment(taskId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: string) =>
      unwrap(api.POST("/tasks/{taskId}/comments", { params: { path: { taskId } }, body: { body } })),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["comments", taskId] });
      void qc.invalidateQueries({ queryKey: ["history", taskId] });
      void qc.invalidateQueries({ queryKey: qk.task(taskId) }); // yorum sayısı
    },
  });
}

export function useTaskHistory(taskId: string) {
  return useQuery({
    queryKey: ["history", taskId],
    queryFn: () => unwrap(api.GET("/tasks/{taskId}/history", { params: { path: { taskId } } })),
  });
}

// ---------------------------------------------------------------- org
export function useTeams() {
  return useQuery({ queryKey: ["teams"], queryFn: () => unwrap(api.GET("/teams")), staleTime: 300_000 });
}

export function useUsers(q: { teamId?: string; q?: string; page?: number; pageSize?: number; isActive?: boolean }) {
  return useQuery({
    queryKey: ["users", q],
    queryFn: () => unwrap(api.GET("/users", { params: { query: q } })),
    placeholderData: keepPreviousData,
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["UserCreate"]) => unwrap(api.POST("/users", { body })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: Schemas["UserUpdate"] & { id: string }) =>
      unwrap(api.PATCH("/users/{userId}", { params: { path: { userId: id } }, body })),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["users"] });
      void qc.invalidateQueries({ queryKey: ["teams"] });
    },
  });
}

export function useUpdateTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: Schemas["TeamUpdate"] & { id: string }) =>
      unwrap(api.PATCH("/teams/{teamId}", { params: { path: { teamId: id } }, body })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["teams"] }),
  });
}

export function useCreateTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["TeamCreate"]) => unwrap(api.POST("/teams", { body })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["teams"] }),
  });
}

// ---------------------------------------------------------------- projects
export function useProjects(q: { teamId?: string; status?: Schemas["ProjectStatus"]; q?: string; page?: number }) {
  return useQuery({
    queryKey: ["projects", q],
    queryFn: () => unwrap(api.GET("/projects", { params: { query: { pageSize: 50, ...q } } })),
    placeholderData: keepPreviousData,
  });
}

export function useProject(id: string | undefined) {
  return useQuery({
    queryKey: ["projects", "one", id],
    queryFn: () => unwrap(api.GET("/projects/{projectId}", { params: { path: { projectId: id! } } })),
    enabled: !!id,
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["ProjectCreate"]) => unwrap(api.POST("/projects", { body })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useUpdateProject(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["ProjectUpdate"]) =>
      unwrap(api.PATCH("/projects/{projectId}", { params: { path: { projectId: id } }, body })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

// ---------------------------------------------------------------- events
export function useEvents(q: { scope?: Schemas["EventScope"]; participantId?: string; q?: string; page?: number }) {
  return useQuery({
    queryKey: ["events", q],
    queryFn: () => unwrap(api.GET("/events", { params: { query: { pageSize: 50, ...q } } })),
    placeholderData: keepPreviousData,
  });
}

export function useParticipations(eventId: string | undefined) {
  return useQuery({
    queryKey: ["participations", eventId],
    queryFn: () =>
      unwrap(api.GET("/events/{eventId}/participations", { params: { path: { eventId: eventId! } } })),
    enabled: !!eventId,
  });
}

function useInvalidateEvents() {
  const qc = useQueryClient();
  return () => {
    void qc.invalidateQueries({ queryKey: ["events"] });
    void qc.invalidateQueries({ queryKey: ["participations"] });
  };
}

export function useCreateEvent() {
  const done = useInvalidateEvents();
  return useMutation({
    mutationFn: (body: Schemas["EventCreate"]) => unwrap(api.POST("/events", { body })),
    onSuccess: done,
  });
}

export function useRequestParticipation() {
  const done = useInvalidateEvents();
  return useMutation({
    mutationFn: ({ eventId, ...body }: Schemas["ParticipationCreate"] & { eventId: string }) =>
      unwrap(api.POST("/events/{eventId}/participations", { params: { path: { eventId } }, body })),
    onSuccess: done,
  });
}

export function useDecideParticipation() {
  const done = useInvalidateEvents();
  return useMutation({
    mutationFn: ({ id, ...body }: Schemas["ParticipationDecision"] & { id: string }) =>
      unwrap(api.PATCH("/participations/{participationId}", { params: { path: { participationId: id } }, body })),
    onSuccess: done,
  });
}

// ---------------------------------------------------------------- competencies
export function useCompetencyCatalog() {
  return useQuery({ queryKey: ["competencies"], queryFn: () => unwrap(api.GET("/competencies")) });
}

export function useUserCompetencies(userId: string | undefined) {
  return useQuery({
    queryKey: ["user-competencies", userId],
    queryFn: () => unwrap(api.GET("/users/{userId}/competencies", { params: { path: { userId: userId! } } })),
    enabled: !!userId,
  });
}

export function useCompetencyMatrix(teamId: string | undefined) {
  return useQuery({
    queryKey: ["competency-matrix", teamId],
    queryFn: () => unwrap(api.GET("/competencies/matrix", { params: { query: { teamId: teamId! } } })),
    enabled: !!teamId,
  });
}

export function useUpsertCompetency() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, competencyId, ...body }: Schemas["UserCompetencyUpsert"] & {
      userId: string;
      competencyId: string;
    }) =>
      unwrap(
        api.PUT("/users/{userId}/competencies/{competencyId}", { params: { path: { userId, competencyId } }, body }),
      ),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["user-competencies"] });
      void qc.invalidateQueries({ queryKey: ["competency-matrix"] });
    },
  });
}

export function useDeleteCompetency() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, competencyId }: { userId: string; competencyId: string }) =>
      unwrap(api.DELETE("/users/{userId}/competencies/{competencyId}", { params: { path: { userId, competencyId } } })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["user-competencies"] }),
  });
}

export function useCreateCatalogItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["CompetencyCreate"]) => unwrap(api.POST("/competencies", { body })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["competencies"] }),
  });
}

// ---------------------------------------------------------------- notifications & announcements
export function useUnreadCount() {
  return useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => unwrap(api.GET("/notifications/unread-count")),
    refetchInterval: 30_000,
  });
}

export function useNotifications(unread?: boolean) {
  return useQuery({
    queryKey: ["notifications", "list", unread],
    queryFn: () => unwrap(api.GET("/notifications", { params: { query: { pageSize: 30, unread } } })),
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id?: string) =>
      id
        ? unwrap(api.POST("/notifications/{notificationId}/read", { params: { path: { notificationId: id } } }))
        : unwrap(api.POST("/notifications/read-all")),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useAnnouncements() {
  return useQuery({
    queryKey: ["announcements"],
    queryFn: () => unwrap(api.GET("/announcements", { params: { query: { pageSize: 50 } } })),
  });
}

export function useCreateAnnouncement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["AnnouncementCreate"]) => unwrap(api.POST("/announcements", { body })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["announcements"] }),
  });
}

export function useDeleteAnnouncement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE("/announcements/{announcementId}", { params: { path: { announcementId: id } } })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["announcements"] }),
  });
}

// ---------------------------------------------------------------- api tokens
export function useApiTokens() {
  return useQuery({ queryKey: ["api-tokens"], queryFn: () => unwrap(api.GET("/me/api-tokens")) });
}

export function useCreateApiToken() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["ApiTokenCreate"]) => unwrap(api.POST("/me/api-tokens", { body })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["api-tokens"] }),
  });
}

export function useRevokeApiToken() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => unwrap(api.DELETE("/me/api-tokens/{tokenId}", { params: { path: { tokenId: id } } })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["api-tokens"] }),
  });
}

// ---------------------------------------------------------------- audit, security, system
export function useAuditLogs(q: { page?: number; action?: string; entityType?: string }) {
  return useQuery({
    queryKey: ["audit", q],
    queryFn: () =>
      unwrap(api.GET("/audit-logs", { params: { query: { pageSize: 25, ...q } } })) as Promise<
        Schemas["AuditLogPage"]
      >,
    placeholderData: keepPreviousData,
  });
}

export function useSecuritySummary(window: "1h" | "24h" | "7d") {
  return useQuery({
    queryKey: ["security-summary", window],
    queryFn: () => unwrap(api.GET("/security/summary", { params: { query: { window } } })),
    refetchInterval: 15_000,
  });
}

export function useSecurityEvents(q: { page?: number; type?: Schemas["SecurityEventType"]; severity?: Schemas["SecuritySeverity"] }) {
  return useQuery({
    queryKey: ["security-events", q],
    queryFn: () => unwrap(api.GET("/security/events", { params: { query: { pageSize: 25, ...q } } })),
    refetchInterval: 15_000,
    placeholderData: keepPreviousData,
  });
}

export function useMetricsSummary(window: "15m" | "1h" | "24h") {
  return useQuery({
    queryKey: ["metrics", window],
    queryFn: () => unwrap(api.GET("/system/metrics-summary", { params: { query: { window } } })),
    refetchInterval: 15_000,
  });
}

// ---------------------------------------------------------------- TASK-019: ilerleme, takip, ekler, öneri
/** multipart yükleme: openapi-fetch JSON odaklı olduğundan fetch + CSRF ile. */
async function upload<T>(path: string, form: FormData): Promise<T> {
  const token = document.cookie
    .split("; ")
    .find((c) => c.startsWith("cth_csrf="))
    ?.slice("cth_csrf=".length);
  const res = await fetch(`/api/v1${path}`, {
    method: "POST",
    body: form,
    credentials: "same-origin",
    headers: token ? { "X-CSRF-Token": decodeURIComponent(token) } : {},
  });
  const body = res.headers.get("content-type")?.includes("json") ? await res.json() : undefined;
  if (!res.ok) throw new ApiError(res.status, body as Schemas["Problem"] | undefined);
  return body as T;
}

export function useTaskProgress(taskId: string) {
  return useQuery({
    queryKey: ["progress", taskId],
    queryFn: () => unwrap(api.GET("/tasks/{taskId}/progress", { params: { path: { taskId } } })),
  });
}

export function useUpdateProgress(taskId: string) {
  const done = useInvalidateTasks();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["TaskProgressUpdate"]) =>
      unwrap(api.POST("/tasks/{taskId}/progress", { params: { path: { taskId } }, body })),
    onSuccess: () => {
      done();
      void qc.invalidateQueries({ queryKey: ["progress", taskId] });
      void qc.invalidateQueries({ queryKey: ["history", taskId] });
    },
  });
}

export function useWatchToggle(taskId: string) {
  const done = useInvalidateTasks();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (on: boolean) =>
      on
        ? unwrap(api.PUT("/tasks/{taskId}/watch", { params: { path: { taskId } } }))
        : unwrap(api.DELETE("/tasks/{taskId}/watch", { params: { path: { taskId } } })),
    onSuccess: () => {
      done();
      void qc.invalidateQueries({ queryKey: ["watchers", taskId] });
    },
  });
}

export function useWatchers(taskId: string) {
  return useQuery({
    queryKey: ["watchers", taskId],
    queryFn: () => unwrap(api.GET("/tasks/{taskId}/watchers", { params: { path: { taskId } } })),
  });
}

export function useAttachments(taskId: string) {
  return useQuery({
    queryKey: ["attachments", taskId],
    queryFn: () => unwrap(api.GET("/tasks/{taskId}/attachments", { params: { path: { taskId } } })),
  });
}

export function useUploadAttachment(taskId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return upload<Schemas["Attachment"]>(`/tasks/${taskId}/attachments`, form);
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["attachments", taskId] });
      void qc.invalidateQueries({ queryKey: qk.task(taskId) });
    },
  });
}

export function useDeleteAttachment(taskId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE("/attachments/{attachmentId}", { params: { path: { attachmentId: id } } })),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["attachments", taskId] });
      void qc.invalidateQueries({ queryKey: qk.task(taskId) });
    },
  });
}

export function useAssignableUsers(teamId?: string) {
  return useQuery({
    queryKey: ["assignable", teamId ?? null],
    queryFn: () => unwrap(api.GET("/me/assignable-users", { params: { query: { teamId } } })),
    staleTime: 60_000,
  });
}

export function useAssigneeSuggestions(category: Schemas["TaskCategory"] | undefined, teamId?: string) {
  return useQuery({
    queryKey: ["suggestions", category, teamId ?? null],
    queryFn: () =>
      unwrap(api.GET("/tasks/assignee-suggestions", { params: { query: { category: category!, teamId } } })),
    enabled: !!category,
    staleTime: 60_000,
  });
}

// ---------------------------------------------------------------- units
export function useUnits() {
  return useQuery({ queryKey: ["units"], queryFn: () => unwrap(api.GET("/units")), staleTime: 300_000 });
}

export function useCreateUnit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["UnitCreate"]) => unwrap(api.POST("/units", { body })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["units"] }),
  });
}

export function useUpdateUnit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: Schemas["UnitUpdate"] & { id: string }) =>
      unwrap(api.PATCH("/units/{unitId}", { params: { path: { unitId: id } }, body })),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["units"] });
      void qc.invalidateQueries({ queryKey: ["teams"] });
    },
  });
}

// ---------------------------------------------------------------- report schedules
export function useReportSchedules() {
  return useQuery({ queryKey: ["report-schedules"], queryFn: () => unwrap(api.GET("/report-schedules")) });
}

export function useCreateReportSchedule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["ReportScheduleCreate"]) => unwrap(api.POST("/report-schedules", { body })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["report-schedules"] }),
  });
}

export function useUpdateReportSchedule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: Schemas["ReportScheduleUpdate"] & { id: string }) =>
      unwrap(api.PATCH("/report-schedules/{scheduleId}", { params: { path: { scheduleId: id } }, body })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["report-schedules"] }),
  });
}

export function useDeleteReportSchedule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE("/report-schedules/{scheduleId}", { params: { path: { scheduleId: id } } })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["report-schedules"] }),
  });
}

export function useRunReportSchedule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.POST("/report-schedules/{scheduleId}/run", { params: { path: { scheduleId: id } } })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["report-schedules"] }),
  });
}

// ---------------------------------------------------------------- project organization
export function useProjectOrganization(projectId: string | undefined) {
  return useQuery({
    queryKey: ["projects", "org", projectId],
    queryFn: () =>
      unwrap(api.GET("/projects/{projectId}/organization", { params: { path: { projectId: projectId! } } })),
    enabled: !!projectId,
  });
}

export function useAddStakeholder(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["ProjectStakeholderCreate"]) =>
      unwrap(api.POST("/projects/{projectId}/stakeholders", { params: { path: { projectId } }, body })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["projects", "org", projectId] }),
  });
}

export function useRemoveStakeholder(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (stakeholderId: string) =>
      unwrap(
        api.DELETE("/projects/{projectId}/stakeholders/{stakeholderId}", {
          params: { path: { projectId, stakeholderId } },
        }),
      ),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["projects", "org", projectId] }),
  });
}

// ---------------------------------------------------------------- certifications & event photos
export function useCertifications(userId: string | undefined) {
  return useQuery({
    queryKey: ["certifications", userId],
    queryFn: () => unwrap(api.GET("/users/{userId}/certifications", { params: { path: { userId: userId! } } })),
    enabled: !!userId,
  });
}

export function useAddCertification(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["CertificationCreate"]) =>
      unwrap(api.POST("/users/{userId}/certifications", { params: { path: { userId } }, body })),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["certifications", userId] });
      void qc.invalidateQueries({ queryKey: ["user-competencies"] });
      void qc.invalidateQueries({ queryKey: ["competency-matrix"] });
    },
  });
}

export function useDeleteCertification(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE("/certifications/{certificationId}", { params: { path: { certificationId: id } } })),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["certifications", userId] }),
  });
}

export function useEventPhotos(eventId: string | undefined) {
  return useQuery({
    queryKey: ["event-photos", eventId],
    queryFn: () => unwrap(api.GET("/events/{eventId}/photos", { params: { path: { eventId: eventId! } } })),
    enabled: !!eventId,
  });
}

export function useUploadEventPhoto(eventId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ file, caption }: { file: File; caption?: string }) => {
      const form = new FormData();
      form.append("file", file);
      if (caption) form.append("caption", caption);
      return upload<Schemas["EventPhoto"]>(`/events/${eventId}/photos`, form);
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["event-photos", eventId] });
      void qc.invalidateQueries({ queryKey: ["events"] });
    },
  });
}

export function useDeleteEventPhoto(eventId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE("/event-photos/{photoId}", { params: { path: { photoId: id } } })),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["event-photos", eventId] });
      void qc.invalidateQueries({ queryKey: ["events"] });
    },
  });
}

export function useUpdateEvent(eventId: string) {
  const done = useInvalidateEvents();
  return useMutation({
    mutationFn: (body: Schemas["EventUpdate"]) =>
      unwrap(api.PATCH("/events/{eventId}", { params: { path: { eventId } }, body })),
    onSuccess: done,
  });
}

/** CSV indirme: sözleşmedeki aynı uç nokta `format=csv` ile; tarayıcı indirmesi olarak. */
export function csvUrl(path: "/reports/tasks" | "/audit-logs", query: Record<string, string | undefined>): string {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(query)) if (v) qs.set(k, v);
  qs.set("format", "csv");
  return `/api/v1${path}?${qs.toString()}`;
}

export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    const field = err.problem?.errors?.[0];
    if (field) return `${field.field}: ${field.message}`;
    if (err.status === 403) return err.problem?.detail ?? "Bu işlem için yetkiniz yok.";
    if (err.status === 409) return err.problem?.detail ?? "Kayıt başka biri tarafından değiştirildi.";
    return err.message;
  }
  return "Beklenmeyen bir hata oluştu. Bağlantınızı kontrol edin.";
}

export { ApiError };
