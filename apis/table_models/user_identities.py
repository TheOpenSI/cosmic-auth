from sqlmodel import Field, Relationship
from sqlalchemy.schema import (
    PrimaryKeyConstraint,
    UniqueConstraint,
    ForeignKeyConstraint,
)
from datetime import datetime, timezone
from uuid import UUID, uuid7
from sqlalchemy.sql.sqltypes import TIMESTAMP, Uuid
from typing import TYPE_CHECKING, Optional

from ..base_models import UserIdentityBase

if TYPE_CHECKING:
    from .users import Users


class UserIdentities(UserIdentityBase, table=True):
    __tablename__: str = "user_identities"  # pyright: ignore
    __table_args__ = (
        PrimaryKeyConstraint("id", name="PK_USER_IDENTITY_ID"),
        UniqueConstraint("provider", "sub", name="UK_USER_IDENTITY_PROVIDER_SUB"),
        ForeignKeyConstraint(
            columns=["user_id"],
            refcolumns=["users.id"],
            name="FK_USER_IDENTITY_USER_ID",
            onupdate="CASCADE",
            ondelete="CASCADE",
            match="FULL",
        ),
    )

    id: UUID = Field(
        default_factory=(lambda: uuid7()),
        nullable=False,
        sa_type=Uuid(as_uuid=True, native_uuid=True),  # pyright: ignore
    )
    created_on: datetime = Field(
        default_factory=(lambda: datetime.now(tz=timezone.utc)),
        nullable=False,
        sa_type=TIMESTAMP(timezone=True),  # pyright: ignore
    )

    user: Optional["Users"] = Relationship(back_populates="identities")