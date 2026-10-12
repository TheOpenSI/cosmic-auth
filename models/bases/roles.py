### Core modules ###
from sqlmodel import (
    Field,
    SQLModel
)


### Type hints ###
from sqlalchemy.sql.sqltypes import (
    VARCHAR,
    Text
)


### Internal modules ###



"""
To understand how this file structured, take a look at:
https://fastapi.tiangolo.com/tutorial/sql-databases/#update-the-app-with-multiple-models
"""
class RoleBase(SQLModel):
    name: str = Field(
        max_length=255,
        nullable=False,
        sa_type=VARCHAR(
            length=255,
            collation=None
        ) # pyright: ignore[reportArgumentType]
    )
    desc: str | None = Field(
        default=None,
        nullable=True,
        sa_type=Text(
            length=None,
            collation=None
        ) # pyright: ignore[reportArgumentType]
    )
