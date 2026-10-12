"""The single Cosmic claim shape produced from an IdP login."""

### Core modules ###
from dataclasses import (
    dataclass,
    field
)


### Type hints ###


### Internal modules ###


@dataclass
class NormalisedClaims:
    provider:   str
    sub:        str
    email:      str | None  = None
    name:       str | None  = None
    roles:      list[str]   = field(default_factory=list[str])
