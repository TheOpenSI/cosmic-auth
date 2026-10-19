"""
The single CoSMIC claim shape produced from an IdP login.
"""


### Core modules ###
from pydantic import BaseModel


### Type hints ###


### Internal modules ###


class NormalisedClaims(BaseModel):
    provider:   str
    sub:        str
    email:      str
    name:       str
    roles:      list[str]
