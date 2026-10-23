### Core modules ###
from pydantic import (
    BaseModel,
    ConfigDict
)


### Type hints ###
from typing import ClassVar


### Internal modules ###


class RolePublic(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    name:   str
    desc:   str | None = None


class RoleCreate(RolePublic):
    pass


class RoleUpdate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    name:   str | None = None
    desc:   str | None = None


class RoleDelete(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    name:   str
