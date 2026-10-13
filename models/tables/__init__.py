"""
Table models required by CoSMIC Auth micro-service.


SQLAlchemy configures every mapper in a registry together. Further explaining
this, a ``relationship()`` declared on one model makes the *other* model
mandatory at configure time even when this service never queries it. This module
is therefore the single place where the table models are imported, so importing
``models.tables`` is always enough for a query to work.
"""


### Core modules ###


### Type hints ###


### Internal modules ###
from .roles import Roles
from .user_identities import UserIdentities
from .users import Users


__all__: list[str] = [
    "Roles",
    "UserIdentities",
    "Users"
]
