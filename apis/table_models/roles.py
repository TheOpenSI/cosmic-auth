### Core modules ###
from sqlmodel import (
    Field,
    Relationship
)
from sqlalchemy.schema import (
    PrimaryKeyConstraint,
    UniqueConstraint
)


### Type hints ###
from datetime import (
    datetime,
    timezone
)
from uuid import UUID, uuid7
from sqlalchemy.sql.sqltypes import (
    TIMESTAMP,
    Uuid
)
from typing import (
    TYPE_CHECKING,
    Optional
)


### Internal modules ###
from ..base_models import RoleBase
if TYPE_CHECKING:
    """
    This's to resolve circular import issues, take a look at:
    https://sqlmodel.tiangolo.com/tutorial/code-structure/#circular-imports
    """
    from .users import Users



"""
To understand how this file structured, take a look at:
https://fastapi.tiangolo.com/tutorial/sql-databases/#update-the-app-with-multiple-models
"""
class Roles(RoleBase, table=True):
    __tablename__: str = "roles" # pyright: ignore
    __table_args__: tuple[
        PrimaryKeyConstraint,
        UniqueConstraint
    ] = (
        PrimaryKeyConstraint(
            "id",
            name="PK_ROLE_ID"
        ),
        UniqueConstraint(
            "name",
            name="UK_ROLE_NAME"
        ),
    )

    id: UUID = Field(
        default_factory=(lambda: uuid7()),
        nullable=False,
        sa_type=Uuid(
            as_uuid=True,
            native_uuid=True
        ) # pyright: ignore
    )
    create_on: datetime = Field(
        default_factory=(lambda: datetime.now(tz=timezone.utc)),
        nullable=False,
        sa_type=TIMESTAMP(timezone=True) # pyright: ignore
    )

    """
    https://sqlmodel.tiangolo.com/tutorial/relationship-attributes/
    """
    user: Optional["Users"] = Relationship(
        back_populates="role"
    )
