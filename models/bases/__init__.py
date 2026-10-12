### Core modules ###
from sqlmodel import (
    Field,
    SQLModel
)


### Type hints ###
from uuid import UUID
from sqlalchemy.sql.sqltypes import (
    VARCHAR,
    Text,
    Uuid
)


### Internal modules ###



"""
To understand how this file structured, take a look at:
https://fastapi.tiangolo.com/tutorial/sql-databases/#update-the-app-with-multiple-models
"""
class UserBase(SQLModel):
    role_id: UUID = Field(
        nullable=False,
        sa_type=Uuid(
            as_uuid=True,
            native_uuid=True
        ) # pyright: ignore
    )
    name: str = Field(
        max_length=255,
        nullable=False,
        sa_type=VARCHAR(
            length=255,
            collation=None
        ) # pyright: ignore
    )


class RoleBase(SQLModel):
    name: str = Field(
        max_length=255,
        nullable=False,
        sa_type=VARCHAR(
            length=255,
            collation=None
        ) # pyright: ignore
    )
    desc: str | None = Field(
        default=None,
        nullable=True,
        sa_type=Text(
            length=None,
            collation=None
        ) # pyright: ignore
    )


class UserIdentityBase(SQLModel):
    user_id: UUID = Field(
        nullable=False,
        sa_type=Uuid(as_uuid=True, native_uuid=True),  # pyright: ignore
    )
    provider: str = Field(
        max_length=50,
        nullable=False,
        sa_type=VARCHAR(length=50, collation=None),  # pyright: ignore
    )
    sub: str = Field(
        max_length=255,
        nullable=False,
        sa_type=VARCHAR(length=255, collation=None),  # pyright: ignore
    )
