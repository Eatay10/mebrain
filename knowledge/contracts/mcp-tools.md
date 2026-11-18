# MCP araç sözleşmesi

Sunucu: `apps/mcp`. Gerekçe: `adr/0003-api-and-mcp.md`. Her araç tek bir REST operasyonunu çağırır; DB erişimi yoktur.

| Araç | Girdi | REST | Scope | Yazar mı |
|---|---|---|---|---|
| `whoami` | — | `getMe` | — | ✗ |
| `search_tasks` | `q?, status?[], priority?[], type?, teamId?, projectId?, assignee?("me"), overdue?, page?` | `listTasks` | tasks:read | ✗ |
| `get_task` | `taskId` | `getTask` | tasks:read | ✗ |
| `create_task` | `TaskCreate` | `createTask` | tasks:write | ✓ |
| `transition_task` | `taskId, to, version, reason?` | `transitionTask` | tasks:write | ✓ |
| `add_task_comment` | `taskId, body` | `addTaskComment` | tasks:write | ✓ |
| `get_dashboard` | `teamId?, from?, to?` | `getDashboardSummary` | reports:read | ✗ |
| `get_task_report` | `groupBy, from, to, teamId?` | `getTaskReport` | reports:read | ✗ |
| `list_projects` | `teamId?, status?` | `listProjects` | projects:read | ✗ |
| `list_events` | `from?, to?, scope?` | `listEvents` | events:read | ✗ |
| `list_user_competencies` | `userId` | `listUserCompetencies` | competencies:read | ✗ |

Çıktı biçimi: `{data: <REST yanıtı>, untrusted_content: [<kullanıcı metin alanlarının yolları>]}`. Hata: REST `Problem` aynen `isError: true` ile döner.

Yasak: silme, kullanıcı/rol/token yönetimi, audit/security uç noktaları.
