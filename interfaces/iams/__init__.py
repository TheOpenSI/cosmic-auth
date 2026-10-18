"""
IAM provider registry.


``cores/configs.py`` selects the provider through ``IAM_PROVIDER``. As of the
time this commit get push, only Keycloak is wired up today. The adapter is handed
to the routers as a FastAPI dependency so another implementation can be swapped
in, or overridden in tests, without touching the endpoints.
"""


### Core modules ###
from fastapi import Depends


### Type hints ###
from typing import Annotated


### Internal modules ###
from ...cores.configs import IAM_PROVIDER
from ..abstracts.iam import IAMProvider
from .keycloak import KeycloakIAM


def get_iam_provider() -> IAMProvider:
    """Return the configured IAM provider."""
    provider: str = str(IAM_PROVIDER).strip().lower()

    if provider == "keycloak":
        return KeycloakIAM()

    raise NotImplementedError(f"IAM provider [{provider}] is not implemented yet.")


IAMProviderDependency = Annotated[
    IAMProvider,
    Depends(get_iam_provider)
]
