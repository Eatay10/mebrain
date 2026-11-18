"""Ortak yardımcılar: sayfalama ve ORM → sözleşme dönüşümleri."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Query

from app import contract as c
from app.models import User


@dataclass
class PageParams:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def page_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> PageParams:
    return PageParams(page, page_size)


def user_ref(u: User | None) -> c.UserRef | None:
    return c.UserRef(id=u.id, full_name=u.full_name) if u else None


def to_user(u: User) -> c.User:
    return c.User(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        title=u.title,
        role=u.role,
        team_id=u.team_id,
        team_name=u.team.name if u.team else None,
        unit_id=u.team.unit_id if u.team else None,
        unit_name=u.team.unit.name if u.team and u.team.unit else None,
        is_active=u.is_active,
        last_login_at=u.last_login_at,
    )
