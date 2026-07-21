from fastapi import HTTPException

from auth.providers.base import NormalizedClaims, TokenBundle


class GoogleProvider:
    name = "google"

    def authorize_url(self, state: str, redirect_uri: str) -> str:
        raise HTTPException(
            status_code=501,
            detail="Google provider not implemented yet (Phase 2)",
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> TokenBundle:
        raise HTTPException(
            status_code=501,
            detail="Google provider not implemented yet (Phase 2)",
        )

    def normalize_claims(self, tokens: TokenBundle) -> NormalizedClaims:
        raise HTTPException(
            status_code=501,
            detail="Google provider not implemented yet (Phase 2)",
        )

    async def logout(self, refresh_token: str | None) -> None:
        return None