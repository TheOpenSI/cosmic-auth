### Core modules ###
from fastapi import (
    APIRouter,
    status
)


### Type hints ###


### Internal modules ###
from ...utils.keys import jwk_set


jwks_router: APIRouter = APIRouter(
    tags=["Service Endpoints"]
)


@jwks_router.get(
    path="/jwks.json",
    status_code=status.HTTP_200_OK
)
async def jwks() -> dict[str, list[dict[str, str | list[str]]]]:
    """Public JWKS so the other CoSMIC microservices can verify the session."""
    return jwk_set()
