### Core modules ###
from pydantic import (
    BaseModel,
    ConfigDict
)


### Type hints ###
from typing import ClassVar


### Internal modules ###
from ..datas.users import UserDelete, UserPublic


"""
Client responses format according to FE requirements.
"""
class UserUpdateResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    success:    bool
    updated:    UserPublic


class UserDeleteResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    success:    bool
    deleted:    UserDelete
