from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import contract as c
from app.auth.deps import SessionOnly, current_user, require_scope
from app.db import get_db
from app.models import User
from app.modules.competencies import service

router = APIRouter(tags=["Competencies"])
READ = [Depends(require_scope("competencies:read"))]


@router.get(
    "/competencies", operation_id="listCompetencies", response_model=list[c.Competency], dependencies=READ
)
def list_competencies(_: User = Depends(current_user), db: Session = Depends(get_db)) -> list[c.Competency]:
    return service.catalog(db)


@router.post(
    "/competencies",
    operation_id="createCompetency",
    response_model=c.Competency,
    status_code=201,
    dependencies=[SessionOnly],
)
def create_competency(
    body: c.CompetencyCreate, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> c.Competency:
    return service.create(db, user, body)


@router.get(
    "/competencies/matrix",
    operation_id="getCompetencyMatrix",
    response_model=c.CompetencyMatrix,
    dependencies=READ,
)
def competency_matrix(
    team_id: Annotated[UUID, Query(alias="teamId")],
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.CompetencyMatrix:
    return service.matrix(db, user, team_id)


@router.get(
    "/users/{userId}/competencies",
    operation_id="listUserCompetencies",
    response_model=list[c.UserCompetency],
    dependencies=READ,
)
def list_user_competencies(
    userId: UUID,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> list[c.UserCompetency]:
    return service.list_for_user(db, user, userId)


@router.put(
    "/users/{userId}/competencies/{competencyId}",
    operation_id="upsertUserCompetency",
    response_model=c.UserCompetency,
    dependencies=[SessionOnly],
)
def upsert_user_competency(
    userId: UUID,
    competencyId: UUID,
    body: c.UserCompetencyUpsert,  # noqa: N803
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.UserCompetency:
    return service.upsert(db, user, userId, competencyId, body)


@router.delete(
    "/users/{userId}/competencies/{competencyId}",
    operation_id="deleteUserCompetency",
    status_code=204,
    dependencies=[SessionOnly],
)
def delete_user_competency(
    userId: UUID,
    competencyId: UUID,
    user: User = Depends(current_user),  # noqa: N803
    db: Session = Depends(get_db),
) -> Response:
    service.remove(db, user, userId, competencyId)
    return Response(status_code=204)


@router.get(
    "/users/{userId}/certifications",
    operation_id="listCertifications",
    response_model=list[c.Certification],
    dependencies=READ,
)
def list_certifications(
    userId: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),  # noqa: N803
) -> list[c.Certification]:
    return service.list_certifications(db, user, userId)


@router.post(
    "/users/{userId}/certifications",
    operation_id="addCertification",
    response_model=c.Certification,
    status_code=201,
    dependencies=[SessionOnly],
)
def add_certification(
    userId: UUID,  # noqa: N803
    body: c.CertificationCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> c.Certification:
    return service.add_certification(db, user, userId, body)


@router.delete(
    "/certifications/{certificationId}",
    operation_id="deleteCertification",
    status_code=204,
    dependencies=[SessionOnly],
)
def delete_certification(
    certificationId: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),  # noqa: N803
) -> Response:
    service.delete_certification(db, user, certificationId)
    return Response(status_code=204)
