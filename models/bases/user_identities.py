### Core modules ###
from sqlmodel import (
    Field,
    SQLModel
)


### Type hints ###
from uuid import UUID
from sqlalchemy.sql.sqltypes import (
    VARCHAR,
    Uuid
)


### Internal modules ###



"""
To understand how this file structured, take a look at:
https://fastapi.tiangolo.com/tutorial/sql-databases/#update-the-app-with-multiple-models
"""
class UserIdentityBase(SQLModel):
    user_id: UUID = Field(
        nullable=False,
        sa_type=Uuid(
            as_uuid=True,
            native_uuid=True
        ) # pyright: ignore[reportArgumentType]
    )
    provider: str = Field(
        max_length=50,
        nullable=False,
        sa_type=VARCHAR(
            length=50,
            collation=None
        ) # pyright: ignore[reportArgumentType]
    )
    sub: str = Field(
        max_length=255,
        nullable=False,
        sa_type=VARCHAR(
            length=255,
            collation=None
        ) # pyright: ignore[reportArgumentType]
    )
