### Core modules ###
from pydantic import (
    BaseModel,
    ConfigDict
)


### Type hints ###
from typing import ClassVar


### Internal modules ###
from ..datas.roles import RoleIAMResult


"""
Client responses format according to FE requirements.
"""
class RoleCreateResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    success:    bool
    created:    RoleIAMResult


class RoleUpdateResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    success:    bool
    updated:    RoleIAMResult


class RoleDeleteResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    success:    bool
    deleted:    RoleIAMResult
