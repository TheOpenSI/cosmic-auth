"""Table models required by the Auth service.


SQLAlchemy configures every mapper in a registry together: a ``relationship()``
declared on one model makes the *other* model mandatory at configure time even
when this service never queries it. This module is therefore the single place
where the table models are imported, so importing ``models.tables`` is always
enough for a query to work.

Unlike ``cosmic-db``, this repository's copy of ``users`` intentionally drops the
``chatboxes`` relationship, since the Auth service never touches that table.
"""

### Core modules ###


### Type hints ###


### Internal modules ###
from .roles import Roles                                     # noqa: F401
from .user_identities import UserIdentities                  # noqa: F401
from .users import Users                                     # noqa: F401


__all__: list[str] = [
    "Roles",
    "UserIdentities",
    "Users"
]
