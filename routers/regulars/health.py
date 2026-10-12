### Core modules ###
from fastapi import (
    APIRouter,
    status
)


### Type hints ###


### Internal modules ###


health_router: APIRouter = APIRouter(
    tags=["Service Endpoints"]
)


@health_router.get(
    path="/health",
    status_code=status.HTTP_200_OK,
    response_model=None
)
async def health() -> dict[str, str]:
    """Liveness probe for Compose, the platform and any orchestrator."""
    return {
        "status": "ok"
    }
