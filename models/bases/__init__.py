"""
Base models required by CoSMIC Auth micro-service.


Each base declares only the columns shared by every CoSMIC service and is
inherited by the matching table model in `models/tables/` (`UserBase` ->
`Users`, `RoleBase` -> `Roles`, `UserIdentityBase` -> `UserIdentities`). This
style of class naming is following the multiple-models pattern of the FastAPI SQL
databases tutorial. Keep the re-exports below in sync with the modules of this
package so the table models can always import them from `models.bases`.
"""


### Core modules ###


### Type hints ###


### Internal modules ###
from .roles import RoleBase
from .user_identities import UserIdentityBase
from .users import UserBase


__all__: list[str] = [
    "RoleBase",
    "UserIdentityBase",
    "UserBase"
]
