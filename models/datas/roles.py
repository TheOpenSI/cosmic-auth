### Core modules ###
from pydantic import (
    BaseModel,
    ConfigDict
)


### Type hints ###
from typing import ClassVar


### Internal modules ###



class RoleCreate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    name:   str
    desc:   str | None = None


class RoleUpdate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    name:   str | None = None
    desc:   str | None = None


class RoleIAMResult(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    name:   str
