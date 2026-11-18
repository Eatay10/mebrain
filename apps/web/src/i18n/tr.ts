/** Türkçe metinler ve enum etiketleri (R-TS-08). */
import type { Schemas } from "@cth/api-client";

export const statusLabel: Record<Schemas["TaskStatus"], string> = {
  TODO: "Başlanmadı",
  IN_PROGRESS: "Devam ediyor",
  BLOCKED: "Bloklu",
  DONE: "Tamamlandı",
};

export const priorityLabel: Record<Schemas["TaskPriority"], string> = {
  LOW: "Düşük",
  MEDIUM: "Orta",
  HIGH: "Yüksek",
  CRITICAL: "Kritik",
};

export const categoryLabel: Record<Schemas["TaskCategory"], string> = {
  INCIDENT_RESPONSE: "Olay müdahale",
  VULNERABILITY_MANAGEMENT: "Zafiyet yönetimi",
  MONITORING: "İzleme",
  PENETRATION_TEST: "Sızma testi",
  COMPLIANCE: "Uyum",
  THREAT_INTEL: "Tehdit istihbaratı",
  AWARENESS: "Farkındalık",
  OPERATIONS: "Operasyon",
  OTHER: "Diğer",
};

export const typeLabel: Record<Schemas["TaskType"], string> = { STANDARD: "Standart", PROJECT: "Proje" };

export const recurrenceLabel: Record<Schemas["Recurrence"], string> = {
  NONE: "Tekrarlanmaz",
  DAILY: "Her iş günü",
  WEEKLY: "Haftalık",
  MONTHLY: "Aylık",
};

export const roleLabel: Record<Schemas["Role"], string> = {
  EMPLOYEE: "Çalışan",
  MANAGER: "Yönetici",
  DIRECTOR: "Direktör",
  AUDITOR: "Denetmen",
};

export const projectStatusLabel: Record<Schemas["ProjectStatus"], string> = {
  ACTIVE: "Aktif",
  ON_HOLD: "Beklemede",
  COMPLETED: "Tamamlandı",
  ARCHIVED: "Arşivlendi",
};

export const eventTypeLabel: Record<Schemas["EventType"], string> = {
  CONFERENCE: "Konferans",
  TRAINING: "Eğitim",
  CTF: "CTF",
  WEBINAR: "Webinar",
  WORKSHOP: "Atölye",
  MEETUP: "Buluşma",
  OTHER: "Diğer",
};

export const eventScopeLabel: Record<Schemas["EventScope"], string> = {
  INDIVIDUAL: "Bireysel",
  CORPORATE: "Kurumsal",
};

export const participationStatusLabel: Record<Schemas["ParticipationStatus"], string> = {
  REQUESTED: "Talep edildi",
  APPROVED: "Onaylandı",
  REJECTED: "Reddedildi",
  ATTENDED: "Katıldı",
  CANCELLED: "İptal",
};

export const participationRoleLabel: Record<Schemas["ParticipationRole"], string> = {
  ATTENDEE: "Katılımcı",
  SPEAKER: "Konuşmacı",
  ORGANIZER: "Organizatör",
  INSTRUCTOR: "Eğitmen",
};

export const competencyCategoryLabel: Record<Schemas["CompetencyCategory"], string> = {
  OFFENSIVE: "Ofansif",
  DEFENSIVE: "Defansif",
  GRC: "GRC",
  CLOUD: "Bulut",
  APPSEC: "Uygulama güvenliği",
  FORENSICS: "Adli bilişim",
  NETWORK: "Ağ",
  OTHER: "Diğer",
};

export const scopeLabel: Record<Schemas["ApiScope"], string> = {
  "tasks:read": "Task okuma",
  "tasks:write": "Task yazma",
  "projects:read": "Proje okuma",
  "reports:read": "Dashboard ve rapor",
  "events:read": "Etkinlik okuma",
  "events:write": "Etkinlik yazma",
  "competencies:read": "Yetkinlik okuma",
};

export const groupByLabel = {
  team: "Ekip",
  assignee: "Kişi",
  project: "Proje",
  status: "Durum",
  priority: "Öncelik",
  category: "Kategori",
  type: "Tür",
} as const;
