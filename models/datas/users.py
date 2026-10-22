### Core modules ###
from pydantic import (
    BaseModel,
    ConfigDict
)


### Type hints ###
from uuid import UUID
from pydantic.networks import EmailStr
from pydantic.types import UUID7
from typing import ClassVar


### Internal modules ###


class UserPublic(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    user_id:        UUID7
    iam_user_id:    str | None = None


class UserUpdate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    role_id:    UUID | None         = None
    name:       str | None          = None
    email:      EmailStr | None     = None


class UserDelete(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    user_id:    UUID7
