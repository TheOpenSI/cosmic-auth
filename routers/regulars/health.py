### Core modules ###
from fastapi import (
    APIRouter,
    status
)


### Type hints ###
from ...cores.tags import APITag


### Internal modules ###


health_router: APIRouter = APIRouter(
    tags=[APITag.regular]
)


@health_router.get(
    path="/health",
    status_code=status.HTTP_200_OK,
    response_model=None
)
async def health() -> dict[str, str]:
    """Liveness probe all compose files, the platform and any orchestrator."""
    return {
        "status": "ok"
    }
