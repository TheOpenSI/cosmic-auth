### Core modules ###
from fastapi import (
    APIRouter,
    status
)


### Type hints ###
from ...cores.tags import APITag


### Internal modules ###
from ...utils.keys import jwk_set


jwks_router: APIRouter = APIRouter(
    tags=[APITag.regular]
)


@jwks_router.get(
    path="/jwks.json",
    status_code=status.HTTP_200_OK
)
async def jwks() -> dict[str, list[dict[str, str | list[str]]]]:
    """Public JWKS so the other CoSMIC micro-services can verify the session."""
    return jwk_set()
