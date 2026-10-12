### Core modules ###
from sqlmodel import (
    Field,
    Relationship
)
from sqlalchemy.schema import (
    PrimaryKeyConstraint,
    UniqueConstraint,
    ForeignKeyConstraint
)


### Type hints ###
from datetime import (
    datetime,
    timezone
)
from uuid import (
    UUID,
    uuid7
)
from sqlalchemy.sql.sqltypes import (
    TIMESTAMP,
    Uuid
)
from typing import (
    TYPE_CHECKING,
    Optional
)


### Internal modules ###
from ..bases import UserIdentityBase
if TYPE_CHECKING:
    """
    This's to resolve circular import issues, take a look at:
    https://sqlmodel.tiangolo.com/tutorial/code-structure/#circular-imports
    """
    from .users import Users


class UserIdentities(UserIdentityBase, table=True):
    __tablename__: str = "user_identities" # pyright: ignore[reportIncompatibleVariableOverride]
    __table_args__: tuple[
        PrimaryKeyConstraint,
        ForeignKeyConstraint,
        UniqueConstraint
    ] = (
        PrimaryKeyConstraint(
            "id",
            name="PK_USER_IDENTITY_ID"
        ),
        ForeignKeyConstraint(
            columns=["user_id"],
            refcolumns=["users.id"],
            name="FK_USER_IDENTITY_USER_ID",
            onupdate="CASCADE",
            ondelete="CASCADE",
            match="FULL"
        ),
        UniqueConstraint(
            "provider",
            "sub",
            name="UK_USER_IDENTITY_PROVIDER_SUB"
        )
    )

    id: UUID = Field(
        default_factory=(lambda: uuid7()),
        nullable=False,
        sa_type=Uuid(
            as_uuid=True,
            native_uuid=True
        ) # pyright: ignore[reportArgumentType]
    )
    created_on: datetime = Field(
        default_factory=(lambda: datetime.now(tz=timezone.utc)),
        nullable=False,
        sa_type=TIMESTAMP(timezone=True) # pyright: ignore[reportArgumentType]
    )

    """
    https://sqlmodel.tiangolo.com/tutorial/relationship-attributes/
    """
    user: Optional["Users"] = Relationship(
        back_populates="identities"
    )
