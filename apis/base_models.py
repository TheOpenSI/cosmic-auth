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
    Uuid,
    Boolean
)
from sqlalchemy.dialects.postgresql import JSONB
from ..types.json_schemas import (
    ChatHistorySchema,
    ConfigurationSchema
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


class ServiceBase(SQLModel):
    name: str = Field(
        max_length=100,
        nullable=False,
        sa_type=VARCHAR(
            length=100,
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
    status: bool = Field(
        default=True,
        nullable=False,
        sa_type=Boolean(
            create_constraint=False,
            name=None
        ) # pyright: ignore
    )
    memory_capability: bool = Field(
        default=False,
        nullable=False,
        sa_type=Boolean(
            create_constraint=False,
            name=None
        ) # pyright: ignore
    )


class ConfigurationBase(SQLModel):
    name: str | None = Field(
        default=None,
        nullable=True,
        sa_type=Text(
            length=None,
            collation=None
        ) # pyright: ignore
    )
    details: ConfigurationSchema = Field(
        nullable=False,
        sa_type=JSONB(
            none_as_null=True,
            astext_type=None
        ) # pyright: ignore
    )


class ChatboxBase(SQLModel):
    user_id: UUID = Field(
        nullable=False,
        sa_type=Uuid(
            as_uuid=True,
            native_uuid=True
        ) # pyright: ignore
    )
    name: str = Field(
        max_length=255,
        nullable=False,
        sa_type=Text(
            length=None,
            collation=None
        ) # pyright: ignore
    )
    details: list[ChatHistorySchema] = Field(
        nullable=False,
        sa_type=JSONB(
            none_as_null=True,
            astext_type=None
        ) # pyright: ignore
    )


class EmissionBase(SQLModel):
    user_id: UUID = Field(
        nullable=False,
        sa_type=Uuid(
            as_uuid=True,
            native_uuid=True
        ) # pyright: ignore
    )
    run_id: UUID = Field(
        nullable=False,
        sa_type=Uuid(
            as_uuid=True,
            native_uuid=True
        ) # pyright: ignore
    )
    duration: float = Field(
        nullable=False
    )
    emissions: float = Field(
        nullable=False
    )
    emissions_rate: float = Field(
        nullable=False
    )
    cpu_power: float = Field(
        nullable=False
    )
    gpu_power: float = Field(
        nullable=False
    )
    ram_power: float = Field(
        nullable=False
    )
    cpu_energy: float = Field(
        nullable=False
    )
    gpu_energy: float = Field(
        nullable=False
    )
    ram_energy: float = Field(
        nullable=False
    )
    energy_consumed: float = Field(
        nullable=False
    )
    water_consumed: float = Field(
        nullable=False
    )
    region: str | None = Field(
        default=None,
        max_length=255,
        nullable=False,
        sa_type=VARCHAR(
            length=255,
            collation=None
        ) # pyright: ignore
    )
    cloud_provider: str | None = Field(
        default=None,
        max_length=255,
        nullable=False,
        sa_type=VARCHAR(
            length=255,
            collation=None
        ) # pyright: ignore
    )
    cloud_region: str | None = Field(
        default=None,
        max_length=255,
        nullable=False,
        sa_type=VARCHAR(
            length=255,
            collation=None
        ) # pyright: ignore
    )
    os: str | None = Field(
        default=None,
        max_length=255,
        nullable=False,
        sa_type=VARCHAR(
            length=255,
            collation=None
        ) # pyright: ignore
    )
    cpu_count: int | None = Field(
        default=None,
        nullable=False
    )
    cpu_model: str | None = Field(
        default=None,
        max_length=255,
        nullable=False,
        sa_type=VARCHAR(
            length=255,
            collation=None
        ) # pyright: ignore
    )
    gpu_count: int | None = Field(
        default=None,
        nullable=False
    )
    gpu_model: str | None = Field(
        default=None,
        max_length=255,
        nullable=False,
        sa_type=VARCHAR(
            length=255,
            collation=None
        ) # pyright: ignore
    )
    longitude: float | None = Field(
        default=None,
        nullable=False
    )
    latitude: float | None = Field(
        default=None,
        nullable=False
    )
    ram_total_size: float | None = Field(
        default=None,
        nullable=False
    )
    tracking_mode: str | None = Field(
        default=None,
        max_length=50,
        nullable=True,
        sa_type=VARCHAR(
            length=50,
            collation=None
        ) # pyright: ignore
    )
    cpu_utilization_percent: float | None = Field(
        default=None,
        nullable=False
    )
    gpu_utilization_percent: float | None = Field(
        default=None,
        nullable=False
    )
    ram_utilization_percent: float | None = Field(
        default=None,
        nullable=False
    )
    ram_used_gb: float | None = Field(
        default=None,
        nullable=False
    )
    on_cloud: str | None = Field(
        default=None,
        max_length=1,
        nullable=False,
        sa_type=VARCHAR(
            length=1,
            collation=None
        ) # pyright: ignore
    )
    pue: float | None = Field(
        default=None,
        nullable=False
    )
    wue: float | None = Field(
        default=None,
        nullable=False
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
