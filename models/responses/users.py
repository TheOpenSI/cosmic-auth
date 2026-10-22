### Core modules ###
from pydantic import (
    BaseModel,
    ConfigDict
)


### Type hints ###
from typing import ClassVar


### Internal modules ###
from ..datas.users import UserIAMResult


"""
Client responses format according to FE requirements.
"""
class UserUpdateResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    success:    bool
    updated:    UserIAMResult


class UserDeleteResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    success:    bool
    deleted:    UserIAMResult
