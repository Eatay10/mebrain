"""Deterministik demo verisi — SADECE sentetik veri (KVKK).

Kullanım: `python -m app.seed [--reset]`. Owner bağlantısıyla (MIGRATION_DATABASE_URL) çalışır.
Tüm demo hesaplarının parolası CTH_SEED_PASSWORD ortam değişkeninden gelir.
"""

import argparse
import random
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.config import get_settings
from app.contract import (
    CompetencyCategory as CC,
)
from app.contract import (
    EventScope,
    EventType,
    ParticipationRole,
    ParticipationStatus,
    ProjectStatus,
    Recurrence,
    Role,
    StakeholderRole,
    TaskCategory,
    TaskPriority,
    TaskStatus,
    TaskType,
)
from app.models import (
    Announcement,
    Certification,
    Competency,
    CompetencyScoreLog,
    Event,
    EventCompetency,
    EventParticipation,
    Project,
    ProjectStakeholder,
    Task,
    TaskComment,
    TaskProgressEntry,
    TaskWatcher,
    Team,
    Unit,
    User,
    UserCompetency,
)

RNG = random.Random(2026)
NOW = datetime.now(UTC).replace(microsecond=0)
TODAY = NOW.date()

FIRST = [
    "Ayşe",
    "Mehmet",
    "Zeynep",
    "Can",
    "Elif",
    "Burak",
    "Selin",
    "Emre",
    "Deniz",
    "Ece",
    "Kerem",
    "Defne",
    "Mert",
    "İrem",
    "Onur",
    "Gizem",
    "Tolga",
    "Melis",
    "Barış",
    "Pelin",
    "Arda",
    "Ceren",
    "Kaan",
    "Derya",
    "Umut",
    "Sena",
    "Oğuz",
    "Buse",
    "Serkan",
    "Nazlı",
    "Efe",
    "Yasemin",
    "Ozan",
    "Damla",
    "Cem",
    "Ezgi",
    "Hakan",
    "Aslı",
    "Volkan",
    "Tuğba",
    "Alp",
    "Şule",
    "Berk",
    "Esra",
]
LAST = [
    "Yılmaz",
    "Kaya",
    "Demir",
    "Şahin",
    "Çelik",
    "Yıldız",
    "Aydın",
    "Öztürk",
    "Arslan",
    "Doğan",
    "Kılıç",
    "Aslan",
    "Çetin",
    "Kara",
    "Koç",
    "Kurt",
    "Özdemir",
    "Polat",
    "Erdoğan",
    "Güneş",
    "Aksoy",
    "Tekin",
]

TEAMS = {
    "soc": ("SOC", "Güvenlik Operasyon Merkezi — 7/24 izleme ve olay müdahale", 12),
    "pentest": ("Pentest", "Sızma testleri ve kırmızı takım çalışmaları", 9),
    "grc": ("GRC", "Yönetişim, risk ve uyum", 7),
    "vuln": ("Zafiyet Yönetimi", "Zafiyet tarama, önceliklendirme ve takip", 10),
}
TITLES = {
    "soc": "SOC Analisti",
    "pentest": "Sızma Testi Uzmanı",
    "grc": "GRC Uzmanı",
    "vuln": "Zafiyet Analisti",
}

TASK_TEMPLATES: dict[str, list[tuple[str, TaskCategory]]] = {
    "soc": [
        ("Şüpheli oturum açma alarmını incele", TaskCategory.INCIDENT_RESPONSE),
        ("EDR uyarısı triage: {host}", TaskCategory.INCIDENT_RESPONSE),
        ("Phishing bildirimi analizi #{n}", TaskCategory.INCIDENT_RESPONSE),
        ("SIEM korelasyon kuralını ayarla: {rule}", TaskCategory.MONITORING),
        ("Vardiya devir raporunu hazırla", TaskCategory.OPERATIONS),
        ("IOC listesini SIEM'e aktar", TaskCategory.THREAT_INTEL),
        ("Firewall log anomalisini araştır", TaskCategory.MONITORING),
        ("Olay sonrası değerlendirme notu: INC-{n}", TaskCategory.INCIDENT_RESPONSE),
    ],
    "pentest": [
        ("Web uygulaması sızma testi: {app}", TaskCategory.PENETRATION_TEST),
        ("Bulgu raporunu yaz: {app}", TaskCategory.PENETRATION_TEST),
        ("Retest: kritik bulgu #{n}", TaskCategory.PENETRATION_TEST),
        ("Kapsam toplantısı notları: {app}", TaskCategory.OPERATIONS),
        ("Active Directory saldırı yolu analizi", TaskCategory.PENETRATION_TEST),
        ("Mobil uygulama statik analizi: {app}", TaskCategory.PENETRATION_TEST),
    ],
    "grc": [
        ("ISO 27001 kontrol kanıtlarını topla: A.{n}", TaskCategory.COMPLIANCE),
        ("Risk değerlendirme toplantısı hazırlığı", TaskCategory.COMPLIANCE),
        ("Tedarikçi güvenlik anketini incele: {vendor}", TaskCategory.COMPLIANCE),
        ("Politika revizyonu: {policy}", TaskCategory.COMPLIANCE),
        ("Farkındalık eğitimi içeriği hazırla", TaskCategory.AWARENESS),
        ("KVKK envanter güncellemesi", TaskCategory.COMPLIANCE),
    ],
    "vuln": [
        ("Haftalık zafiyet tarama sonuçlarını önceliklendir", TaskCategory.VULNERABILITY_MANAGEMENT),
        ("CVE-2026-{n} etki analizi", TaskCategory.VULNERABILITY_MANAGEMENT),
        ("Yama takibi: {host}", TaskCategory.VULNERABILITY_MANAGEMENT),
        ("İstisna talebini değerlendir: {app}", TaskCategory.VULNERABILITY_MANAGEMENT),
        ("SLA aşımı raporu hazırla", TaskCategory.OPERATIONS),
        ("Konteyner imaj taraması: {app}", TaskCategory.VULNERABILITY_MANAGEMENT),
    ],
}
FILL = {
    "host": ["SRV-WEB-01", "SRV-DB-03", "WS-1042", "WS-2210", "SRV-APP-07", "FW-EDGE-02"],
    "rule": ["Brute force", "Lateral movement", "DNS tünelleme", "Yetki yükseltme"],
    "app": ["İK Portalı", "Müşteri API", "Mobil Bankacılık", "Intranet", "Tedarik Portalı", "e-İmza Servisi"],
    "vendor": ["Bulut Sağlayıcı A", "Yazılım Tedarikçisi B", "Danışmanlık C"],
    "policy": ["Parola Politikası", "Erişim Kontrol Politikası", "Olay Müdahale Prosedürü"],
}
PROJECTS = {
    "soc": [
        "SIEM Kural Seti Yenileme",
        "SOAR Otomasyon Pilotu",
        "Tehdit Avı Programı Q4",
        "Log Kaynakları Envanteri",
    ],
    "pentest": [
        "Yıllık Dış Ağ Sızma Testi",
        "Mobil Uygulama Güvenlik Değerlendirmesi",
        "Kırmızı Takım Tatbikatı 2026",
        "API Güvenlik Testleri",
    ],
    "grc": ["ISO 27001 Yeniden Belgelendirme", "KVKK Uyum Projesi", "Üçüncü Taraf Risk Programı"],
    "vuln": [
        "Kritik Zafiyet Kapatma Kampanyası",
        "Konteyner Güvenliği",
        "Varlık Envanteri Entegrasyonu",
        "Yama Yönetim Süreci İyileştirme",
    ],
}
COMPETENCIES = [
    ("Web Uygulama Güvenliği", CC.APPSEC),
    ("Sızma Testi", CC.OFFENSIVE),
    ("Kırmızı Takım", CC.OFFENSIVE),
    ("SIEM Yönetimi", CC.DEFENSIVE),
    ("Olay Müdahale", CC.DEFENSIVE),
    ("Tehdit Avcılığı", CC.DEFENSIVE),
    ("Zararlı Yazılım Analizi", CC.FORENSICS),
    ("Dijital Adli Bilişim", CC.FORENSICS),
    ("Bulut Güvenliği (AWS/Azure)", CC.CLOUD),
    ("Kubernetes Güvenliği", CC.CLOUD),
    ("ISO 27001", CC.GRC),
    ("Risk Yönetimi", CC.GRC),
    ("KVKK / Veri Koruma", CC.GRC),
    ("Ağ Güvenliği", CC.NETWORK),
    ("Firewall / IPS", CC.NETWORK),
    ("Güvenli Kod İnceleme", CC.APPSEC),
]
TEAM_COMPS = {
    "soc": [3, 4, 5, 6, 13, 14],
    "pentest": [0, 1, 2, 15, 13, 8],
    "grc": [10, 11, 12, 13],
    "vuln": [0, 8, 9, 13, 15, 11],
}
EVENTS = [
    ("Black Hat Europe 2026", EventType.CONFERENCE, EventScope.CORPORATE, "ExCeL London"),
    ("BSides İstanbul", EventType.CONFERENCE, EventScope.INDIVIDUAL, "İstanbul"),
    ("Siber Güvenlik Haftası Kurum İçi Etkinlik", EventType.MEETUP, EventScope.CORPORATE, "Genel Müdürlük"),
    ("OSCP Hazırlık Eğitimi", EventType.TRAINING, EventScope.INDIVIDUAL, "Online"),
    ("Ulusal CTF Yarışması", EventType.CTF, EventScope.CORPORATE, "Ankara"),
    ("Bulut Güvenliği Webinarı", EventType.WEBINAR, EventScope.INDIVIDUAL, "Online"),
    ("Tehdit Avcılığı Atölyesi", EventType.WORKSHOP, EventScope.CORPORATE, "Eğitim Salonu"),
    ("ISO 27001 Baş Denetçi Eğitimi", EventType.TRAINING, EventScope.INDIVIDUAL, "İstanbul"),
    ("OWASP Türkiye Buluşması", EventType.MEETUP, EventScope.INDIVIDUAL, "İzmir"),
    ("Masa Başı Tatbikat: Fidye Yazılımı", EventType.WORKSHOP, EventScope.CORPORATE, "Kriz Merkezi"),
    ("SANS FOR508 Eğitimi", EventType.TRAINING, EventScope.CORPORATE, "Online"),
    ("Kubernetes Security Summit", EventType.CONFERENCE, EventScope.INDIVIDUAL, "Amsterdam"),
    ("Kurum İçi Capture The Flag", EventType.CTF, EventScope.CORPORATE, "Genel Müdürlük"),
    ("KVKK Güncel Gelişmeler Semineri", EventType.WEBINAR, EventScope.CORPORATE, "Online"),
    ("Zararlı Yazılım Analizi 101", EventType.TRAINING, EventScope.INDIVIDUAL, "Online"),
    ("Ankara Siber Güvenlik Zirvesi", EventType.CONFERENCE, EventScope.CORPORATE, "Ankara"),
    ("Red Team Village Atölyesi", EventType.WORKSHOP, EventScope.INDIVIDUAL, "İstanbul"),
    ("Güvenli Kodlama Bootcamp", EventType.TRAINING, EventScope.CORPORATE, "Eğitim Salonu"),
    ("Yapay Zekâ ve Güvenlik Paneli", EventType.MEETUP, EventScope.INDIVIDUAL, "Online"),
    ("Yıl Sonu Güvenlik Değerlendirme Toplantısı", EventType.OTHER, EventScope.CORPORATE, "Genel Müdürlük"),
]


UNITS = {
    "defense": ("Savunma Operasyonları", "SOC ve zafiyet yönetimi ekiplerini kapsar.", ("soc", "vuln")),
    "offense": ("Ofansif Güvenlik ve Uyum", "Sızma testi ve GRC ekiplerini kapsar.", ("pentest", "grc")),
}
# Etkinlik başlığındaki anahtar kelime → tamamlanınca puanı artan yetkinlikler
EVENT_COMPS = {
    "Black Hat": ["Sızma Testi", "Tehdit Avcılığı"],
    "BSides": ["Web Uygulama Güvenliği", "Tehdit Avcılığı"],
    "OSCP": ["Sızma Testi", "Kırmızı Takım"],
    "CTF": ["Sızma Testi", "Web Uygulama Güvenliği"],
    "Bulut": ["Bulut Güvenliği (AWS/Azure)"],
    "Tehdit Avcılığı": ["Tehdit Avcılığı", "SIEM Yönetimi"],
    "ISO 27001": ["ISO 27001", "Risk Yönetimi"],
    "OWASP": ["Web Uygulama Güvenliği", "Güvenli Kod İnceleme"],
    "Fidye": ["Olay Müdahale", "Dijital Adli Bilişim"],
    "FOR508": ["Dijital Adli Bilişim", "Olay Müdahale"],
    "Kubernetes": ["Kubernetes Güvenliği", "Bulut Güvenliği (AWS/Azure)"],
    "KVKK": ["KVKK / Veri Koruma"],
    "Zararlı Yazılım": ["Zararlı Yazılım Analizi"],
    "Red Team": ["Kırmızı Takım"],
    "Güvenli Kodlama": ["Güvenli Kod İnceleme", "Web Uygulama Güvenliği"],
}
CERTS = [
    ("OSCP", "OffSec", ["Sızma Testi", "Kırmızı Takım"]),
    ("CISSP", "ISC2", ["Risk Yönetimi", "ISO 27001"]),
    ("CEH", "EC-Council", ["Sızma Testi", "Web Uygulama Güvenliği"]),
    ("GCFA", "GIAC", ["Dijital Adli Bilişim", "Zararlı Yazılım Analizi"]),
    ("GCIH", "GIAC", ["Olay Müdahale", "Tehdit Avcılığı"]),
    ("AWS Certified Security – Specialty", "AWS", ["Bulut Güvenliği (AWS/Azure)"]),
    ("CCNP Security", "Cisco", ["Firewall / IPS", "Ağ Güvenliği"]),
    ("ISO 27001 Lead Auditor", "PECB", ["ISO 27001"]),
]
PROGRESS_NOTES = [
    "Kapsam netleştirildi.",
    "Test ortamı doğrulandı.",
    "İlk bulgular raporlandı.",
    "Sistem sahibiyle toplantı yapıldı.",
    "Analiz büyük ölçüde tamamlandı.",
    "Düzeltmeler doğrulanıyor.",
]


def _name(used: set[str]) -> str:
    while True:
        n = f"{RNG.choice(FIRST)} {RNG.choice(LAST)}"
        if n not in used:
            used.add(n)
            return n


def _fill(template: str) -> str:
    out = template
    for key, values in FILL.items():
        out = out.replace("{" + key + "}", RNG.choice(values))
    return out.replace("{n}", str(RNG.randint(100, 999)))


def _user(db: Session, email: str, name: str, role: Role, team: Team | None, title: str, pw: str) -> User:
    u = User(
        email=email,
        full_name=name,
        role=role,
        team_id=team.id if team else None,
        title=title,
        password_hash=pw,
        created_at=NOW - timedelta(days=200),
    )
    db.add(u)
    return u


def _gain(db: Session, user_id: Any, competency_id: Any, points: int, source: str, source_id: Any) -> None:
    uc = db.get(UserCompetency, (user_id, competency_id))
    if uc is None:
        uc = UserCompetency(user_id=user_id, competency_id=competency_id, level=1, score=0)
        db.add(uc)
    uc.score = min(100, (uc.score or 0) + points)
    uc.level = max(uc.level, min(5, (uc.score + 19) // 20))
    db.add(
        CompetencyScoreLog(
            user_id=user_id,
            competency_id=competency_id,
            source_type=source,
            source_id=source_id,
            points=points,
        )
    )
    db.flush()


def _task_times(status: TaskStatus, created: datetime) -> tuple[datetime | None, datetime | None]:
    if status == TaskStatus.TODO:
        return None, None
    started = created + timedelta(hours=RNG.randint(1, 72))
    started = min(started, NOW - timedelta(hours=1))
    if status == TaskStatus.DONE:
        done = started + timedelta(hours=RNG.randint(2, 240))
        return started, min(done, NOW - timedelta(minutes=5))
    return started, None


def seed(db: Session, pw_hash: str) -> dict[str, Any]:
    used: set[str] = set()
    units = {k: Unit(name=v[0], description=v[1]) for k, v in UNITS.items()}
    db.add_all(units.values())
    db.flush()
    unit_of = {team_key: k for k, v in UNITS.items() for team_key in v[2]}
    teams = {k: Team(name=v[0], description=v[1], unit_id=units[unit_of[k]].id) for k, v in TEAMS.items()}
    db.add_all(teams.values())
    db.flush()

    director = _user(
        db, "director@demo.local", "Deniz Aksoy", Role.DIRECTOR, None, "Siber Güvenlik Direktörü", pw_hash
    )
    auditor = _user(db, "auditor@demo.local", "Selin Tekin", Role.AUDITOR, None, "İç Denetçi", pw_hash)
    unit_managers = {
        "defense": _user(
            db,
            "unit.defense@demo.local",
            "Okan Yıldız",
            Role.UNIT_MANAGER,
            None,
            "Savunma Operasyonları Unit Yöneticisi",
            pw_hash,
        ),
        "offense": _user(
            db,
            "unit.offense@demo.local",
            "Gizem Aydın",
            Role.UNIT_MANAGER,
            None,
            "Ofansif Güvenlik ve Uyum Unit Yöneticisi",
            pw_hash,
        ),
    }
    managers = {
        "soc": _user(
            db,
            "manager.soc@demo.local",
            "Kerem Arslan",
            Role.MANAGER,
            teams["soc"],
            "SOC Yöneticisi",
            pw_hash,
        ),
        "pentest": _user(
            db,
            "manager.pentest@demo.local",
            "Elif Çetin",
            Role.MANAGER,
            teams["pentest"],
            "Ofansif Güvenlik Yöneticisi",
            pw_hash,
        ),
        "grc": _user(
            db, "manager.grc@demo.local", "Murat Koç", Role.MANAGER, teams["grc"], "GRC Yöneticisi", pw_hash
        ),
    }
    used |= {director.full_name, auditor.full_name, *(m.full_name for m in managers.values())}
    used |= {m.full_name for m in unit_managers.values()}
    db.flush()
    for k, um in unit_managers.items():
        units[k].manager_id = um.id
    teams["soc"].manager_id = managers["soc"].id
    teams["vuln"].manager_id = managers["soc"].id  # SOC yöneticisi Zafiyet Yönetimi'ni de yönetir
    teams["pentest"].manager_id = managers["pentest"].id
    teams["grc"].manager_id = managers["grc"].id

    members: dict[str, list[User]] = {}
    for key, (_, _, size) in TEAMS.items():
        prefix = {
            "soc": "analyst.soc",
            "pentest": "analyst.pentest",
            "grc": "analyst.grc",
            "vuln": "analyst.vuln",
        }[key]
        members[key] = [
            _user(db, f"{prefix}{i}@demo.local", _name(used), Role.EMPLOYEE, teams[key], TITLES[key], pw_hash)
            for i in range(1, size + 1)
        ]
    members["soc"][-1].is_active = False  # pasif kullanıcı örneği
    db.flush()

    comps = [Competency(name=n, category=cat) for n, cat in COMPETENCIES]
    db.add_all(comps)
    db.flush()
    for key, users in members.items():
        for u in users:
            for idx in RNG.sample(TEAM_COMPS[key], k=min(len(TEAM_COMPS[key]), RNG.randint(3, 5))):
                verified = RNG.random() < 0.5
                db.add(
                    UserCompetency(
                        user_id=u.id,
                        competency_id=comps[idx].id,
                        level=(lvl := RNG.randint(1, 5)),
                        score=max(5, lvl * 20 - RNG.randint(0, 15)),
                        evidence=RNG.choice([None, "Eğitim sertifikası", "OSCP", "CEH", "Proje deneyimi"]),
                        verified_by=managers.get(key, managers["soc"]).id if verified else None,
                        verified_at=NOW - timedelta(days=RNG.randint(1, 60)) if verified else None,
                    )
                )

    projects: dict[str, list[Project]] = {}
    for key, names in PROJECTS.items():
        owner_mgr = managers.get(key, managers["soc"])
        projects[key] = []
        for name in names:
            start = TODAY - timedelta(days=RNG.randint(20, 120))
            p = Project(
                team_id=teams[key].id,
                name=name,
                owner_id=owner_mgr.id,
                created_by=owner_mgr.id,
                status=RNG.choices(
                    [ProjectStatus.ACTIVE, ProjectStatus.ON_HOLD, ProjectStatus.COMPLETED], [0.75, 0.1, 0.15]
                )[0],
                start_date=start,
                due_date=TODAY + timedelta(days=RNG.randint(-10, 90)),
                description=f"{name} kapsamındaki çalışmalar.",
                created_at=NOW - timedelta(days=120),
            )
            db.add(p)
            projects[key].append(p)
    db.flush()

    statuses = [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.DONE]
    weights = [0.28, 0.27, 0.07, 0.38]
    tasks: list[Task] = []
    for key, users in members.items():
        active = [u for u in users if u.is_active]
        mgr = managers.get(key, managers["soc"])
        n_tasks = {"soc": 190, "pentest": 140, "grc": 100, "vuln": 170}[key]
        for _ in range(n_tasks):
            tpl, cat = RNG.choice(TASK_TEMPLATES[key])
            is_project = RNG.random() < 0.4 and projects[key]
            project = RNG.choice(projects[key]) if is_project else None
            status = RNG.choices(statuses, weights)[0]
            created = NOW - timedelta(days=RNG.randint(0, 90), hours=RNG.randint(0, 23))
            started, completed = _task_times(status, created)
            assignee = RNG.choice(active)
            backup = RNG.choice([u for u in active if u.id != assignee.id]) if RNG.random() < 0.45 else None
            if status == TaskStatus.DONE:
                due = created.date() + timedelta(days=RNG.randint(3, 40))
            else:  # açık task'ların ~%15'i gecikmiş, kalanı önümüzdeki 5 haftada
                offset = RNG.randint(-12, -1) if RNG.random() < 0.15 else RNG.randint(0, 35)
                due = TODAY + timedelta(days=offset)
            due = due if RNG.random() < 0.92 else None
            progress = {
                TaskStatus.TODO: 0,
                TaskStatus.IN_PROGRESS: RNG.randrange(10, 90, 5),
                TaskStatus.BLOCKED: RNG.randrange(10, 65, 5),
                TaskStatus.DONE: 100,
            }[status]
            um = unit_managers[unit_of[key]]
            requester = RNG.choices([mgr, um, director, assignee], [0.55, 0.2, 0.1, 0.15])[0]
            t = Task(
                type=TaskType.PROJECT if project else TaskType.STANDARD,
                progress=progress,
                requester_id=requester.id,
                project_id=project.id if project else None,
                team_id=teams[key].id,
                title=_fill(tpl),
                status=status,
                category=cat,
                description="Ayrıntılar ve ilgili kayıtlar ekip kanalında paylaşılmıştır.",
                priority=RNG.choices(list(TaskPriority), [0.2, 0.4, 0.28, 0.12])[0],
                assignee_id=assignee.id,
                backup_assignee_id=backup.id if backup else None,
                due_date=due,
                blocked_reason="Sistem sahibinden erişim onayı bekleniyor."
                if status == TaskStatus.BLOCKED
                else None,
                created_by=mgr.id,
                created_at=created,
                updated_at=completed or started or created,
                started_at=started,
                completed_at=completed,
            )
            db.add(t)
            tasks.append(t)
            pool = [u for u in active if u.id not in (assignee.id, backup.id if backup else None)]
            if pool and RNG.random() < 0.25:
                t.collaborators = RNG.sample(pool, k=min(len(pool), RNG.randint(1, 2)))
    # Rutin (tekrarlayan) şablonlar — worker günlük örnek üretir.
    for key, title, rec, cat in [
        ("soc", "Günlük SIEM alarm gözden geçirmesi", Recurrence.DAILY, TaskCategory.MONITORING),
        ("soc", "Vardiya kontrol listesi", Recurrence.DAILY, TaskCategory.OPERATIONS),
        ("vuln", "Haftalık zafiyet taraması", Recurrence.WEEKLY, TaskCategory.VULNERABILITY_MANAGEMENT),
        ("grc", "Aylık erişim yetkisi gözden geçirmesi", Recurrence.MONTHLY, TaskCategory.COMPLIANCE),
        ("pentest", "Haftalık bulgu durum toplantısı", Recurrence.WEEKLY, TaskCategory.OPERATIONS),
    ]:
        mgr = managers.get(key, managers["soc"])
        active = [u for u in members[key] if u.is_active]
        db.add(
            Task(
                type=TaskType.STANDARD,
                team_id=teams[key].id,
                title=title,
                category=cat,
                recurrence=rec,
                priority=TaskPriority.MEDIUM,
                assignee_id=active[0].id,
                backup_assignee_id=active[1].id,
                created_by=mgr.id,
                created_at=NOW - timedelta(days=30),
            )
        )
    db.flush()

    for t in tasks:
        if t.backup_assignee_id:
            db.add(TaskWatcher(task_id=t.id, user_id=t.backup_assignee_id, created_at=t.created_at))
        if t.progress == 0:
            continue
        steps = sorted(
            RNG.sample(range(5, t.progress, 5), k=min(RNG.randint(0, 2), max(0, t.progress // 5 - 1)))
        )
        values = [*steps, t.progress]
        prev = 0
        for i, v in enumerate(values):
            db.add(
                TaskProgressEntry(
                    task_id=t.id,
                    author_id=t.assignee_id or t.created_by,
                    from_progress=prev,
                    to_progress=v,
                    note="Task tamamlandı." if v == 100 else RNG.choice(PROGRESS_NOTES),
                    created_at=(t.started_at or t.created_at) + timedelta(hours=6 * (i + 1)),
                )
            )
            prev = v
    for mgr in managers.values():  # yöneticiler bazı task'lara yıldız koyar
        own = [t for t in tasks if t.created_by == mgr.id and t.status != TaskStatus.DONE]
        for t in RNG.sample(own, k=min(len(own), 6)):
            db.add(TaskWatcher(task_id=t.id, user_id=mgr.id, created_at=NOW - timedelta(days=2)))

    # Hiyerarşik atamalar: direktör → unit yöneticisi, unit yöneticisi → ekip yöneticisi
    for k, um in unit_managers.items():
        first_team = teams[UNITS[k][2][0]]
        tasks.append(
            Task(
                type=TaskType.STANDARD,
                team_id=first_team.id,
                title=f"{UNITS[k][0]} çeyreklik hedeflerinin belirlenmesi",
                category=TaskCategory.OPERATIONS,
                priority=TaskPriority.HIGH,
                status=TaskStatus.IN_PROGRESS,
                progress=40,
                assignee_id=um.id,
                requester_id=director.id,
                created_by=director.id,
                due_date=TODAY + timedelta(days=21),
                created_at=NOW - timedelta(days=10),
                started_at=NOW - timedelta(days=9),
            )
        )
        for team_key in UNITS[k][2]:
            mgr = managers.get(team_key, managers["soc"])
            tasks.append(
                Task(
                    type=TaskType.STANDARD,
                    team_id=teams[team_key].id,
                    title=f"{teams[team_key].name} kapasite planı",
                    category=TaskCategory.OPERATIONS,
                    priority=TaskPriority.MEDIUM,
                    status=TaskStatus.TODO,
                    assignee_id=mgr.id,
                    requester_id=um.id,
                    created_by=um.id,
                    due_date=TODAY + timedelta(days=14),
                    created_at=NOW - timedelta(days=5),
                )
            )
        db.add_all(tasks[-(1 + len(UNITS[k][2])) :])
    db.flush()

    phrases = [
        "İlk analiz tamamlandı, detaylar ekte.",
        "Sistem sahibine bilgi verildi.",
        "Yarın sabah tekrar kontrol edeceğim.",
        "Benzer bir vaka geçen ay da görülmüştü.",
        "Önceliği yükseltmeyi öneriyorum.",
        "Kapanış için onay bekliyorum.",
    ]
    for t in RNG.sample(tasks, 160):
        for _ in range(RNG.randint(1, 3)):
            db.add(
                TaskComment(
                    task_id=t.id,
                    author_id=t.assignee_id or t.created_by,
                    body=RNG.choice(phrases),
                    created_at=t.created_at + timedelta(hours=RNG.randint(1, 48)),
                )
            )

    everyone = [u for users in members.values() for u in users if u.is_active] + list(managers.values())
    for i, (title, etype, scope, loc) in enumerate(EVENTS):
        start = NOW + timedelta(days=RNG.randint(-60, 75), hours=RNG.randint(8, 16) - NOW.hour)
        ev = Event(
            title=title,
            type=etype,
            scope=scope,
            location=loc,
            organizer="Kurum" if scope == EventScope.CORPORATE else "Dış organizasyon",
            starts_at=start,
            ends_at=start + timedelta(hours=RNG.choice([2, 8, 24, 48])),
            url="https://example.org/etkinlik",
            created_by=director.id if scope == EventScope.CORPORATE else RNG.choice(everyone).id,
            description=f"{title} hakkında bilgilendirme.",
        )
        comp_by_name = {cp.name: cp for cp in comps}
        linked = next((v for key_word, v in EVENT_COMPS.items() if key_word in title), [])
        points = RNG.choice([10, 15, 20])
        ev.competency_links = [
            EventCompetency(competency_id=comp_by_name[n].id, points=points) for n in linked
        ]
        if ev.ends_at < NOW:
            ev.notes = (
                "Öne çıkanlar: yeni saldırı teknikleri, savunma pratikleri ve ekip için uygulanabilir notlar."
            )
        db.add(ev)
        db.flush()
        for u in RNG.sample(everyone, RNG.randint(2, 7)):
            past = ev.ends_at < NOW
            st = RNG.choice(
                [ParticipationStatus.ATTENDED, ParticipationStatus.APPROVED]
                if past
                else [
                    ParticipationStatus.REQUESTED,
                    ParticipationStatus.APPROVED,
                    ParticipationStatus.REJECTED,
                ]
            )
            decider = (
                None
                if st == ParticipationStatus.REQUESTED
                else (
                    managers.get(
                        next((k for k, t in teams.items() if t.id == u.team_id), "soc"), managers["soc"]
                    ).id
                )
            )
            db.add(
                EventParticipation(
                    event_id=ev.id,
                    user_id=u.id,
                    status=st,
                    decided_by=decider,
                    decided_at=NOW - timedelta(days=1) if decider else None,
                    role=RNG.choices(list(ParticipationRole), [0.8, 0.1, 0.05, 0.05])[0],
                )
            )
            if st == ParticipationStatus.ATTENDED:
                for link in ev.competency_links:
                    _gain(db, u.id, link.competency_id, link.points, "EVENT", ev.id)
        _ = i

    comp_by_name = {cp.name: cp for cp in comps}
    for u in [x for users in members.values() for x in users if x.is_active]:
        if RNG.random() < 0.35:
            name, issuer, comp_names = RNG.choice(CERTS)
            cert = Certification(
                user_id=u.id,
                name=name,
                issuer=issuer,
                issued_on=TODAY - timedelta(days=RNG.randint(30, 900)),
                created_by=u.id,
            )
            db.add(cert)
            db.flush()
            for n in comp_names:
                _gain(db, u.id, comp_by_name[n].id, 15, "CERTIFICATION", cert.id)

    for key, plist in projects.items():
        for p in plist:
            db.add(ProjectStakeholder(project_id=p.id, user_id=director.id, role=StakeholderRole.SPONSOR))
            db.add(
                ProjectStakeholder(
                    project_id=p.id,
                    user_id=unit_managers[unit_of[key]].id,
                    role=StakeholderRole.STAKEHOLDER,
                )
            )
            db.add(
                ProjectStakeholder(
                    project_id=p.id,
                    name="BT Altyapı Müdürlüğü",
                    organization="Bilgi Teknolojileri",
                    role=StakeholderRole.STAKEHOLDER,
                    note="Sistem sahibi; değişiklik onayları",
                )
            )
    db.flush()
    db.add_all(
        [
            Announcement(
                scope="ORGANIZATION",
                title="Siber Güvenlik Farkındalık Ayı başlıyor",
                body="Ekim boyunca tüm ekiplerin farkındalık eğitimlerini tamamlaması bekleniyor.",
                author_id=director.id,
                pinned=True,
                created_at=NOW - timedelta(days=3),
            ),
            Announcement(
                scope="TEAM",
                team_id=teams["soc"].id,
                title="Vardiya planı güncellendi",
                body="Gelecek haftanın vardiya planı paylaşılmıştır; lütfen kontrol edin.",
                author_id=managers["soc"].id,
                created_at=NOW - timedelta(days=1),
            ),
            Announcement(
                scope="TEAM",
                team_id=teams["pentest"].id,
                title="Yeni test ortamı erişimi",
                body="Test ortamı VPN profilleri yenilendi.",
                author_id=managers["pentest"].id,
                created_at=NOW - timedelta(days=2),
            ),
        ]
    )
    db.flush()
    return {
        "teams": len(teams),
        "users": len(everyone) + 3 + len(unit_managers),
        "units": len(units),
        "tasks": len(tasks),
        "projects": sum(len(v) for v in projects.values()),
        "events": len(EVENTS),
    }


TABLES = [
    "competency_score_logs",
    "certifications",
    "event_photos",
    "event_competencies",
    "project_stakeholders",
    "attachments",
    "task_progress_entries",
    "task_watchers",
    "task_collaborators",
    "report_schedules",
    "notifications",
    "announcements",
    "user_competencies",
    "competencies",
    "event_participations",
    "events",
    "task_comments",
    "tasks",
    "projects",
    "api_tokens",
    "sessions",
    "audit_logs",
    "security_events",
    "job_runs",
    "users",
    "teams",
    "units",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Tüm tabloları boşaltıp yeniden üret")
    args = parser.parse_args()
    s = get_settings()
    if not s.seed_password:
        sys.exit("CTH_SEED_PASSWORD tanımlı değil.")
    engine = create_engine(s.migration_database_url or s.database_url)
    with Session(engine) as db:
        if args.reset:
            db.execute(text("UPDATE teams SET manager_id = NULL"))
            db.execute(text("UPDATE units SET manager_id = NULL"))
            db.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))
            db.commit()
        if db.scalar(select(User.id).limit(1)):
            print("Veri zaten var; yeniden üretmek için --reset kullanın.")  # noqa: T201
            return
        stats = seed(db, hash_password(s.seed_password))
        db.commit()
    print(f"Seed tamam: {stats}")  # noqa: T201


if __name__ == "__main__":
    main()
