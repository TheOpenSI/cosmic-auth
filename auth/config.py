# config.py — Auth BFF settings (Keycloak + Google)

import os

# ── Shared BFF ──────────────────────────────────────────────────────────────
AUTH_PUBLIC_URL = os.getenv("AUTH_PUBLIC_URL", "http://localhost:8081")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
AUTH_API_PREFIX = "/api/v1/auth"

ENABLED_PROVIDERS = [
    p.strip().lower()
    for p in os.getenv("ENABLED_PROVIDERS", "keycloak,google").split(",")
    if p.strip()
]

SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-only-change-me")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "cosmic_session")
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", "86400"))

# Legacy IdP token cookies (Phase 0–1). Cosmic session comes in Phase 1.
ACCESS_TOKEN_COOKIE = "cosmic_access_token"
REFRESH_TOKEN_COOKIE = "cosmic_refresh_token"
OAUTH_STATE_COOKIE = "cosmic_oauth_state"
OAUTH_PROVIDER_COOKIE = "cosmic_oauth_provider"


def callback_url(provider: str) -> str:
    """Per-provider callback — must match IdP console redirect URI."""
    return f"{AUTH_PUBLIC_URL}{AUTH_API_PREFIX}/callback/{provider}"


# ── Keycloak ────────────────────────────────────────────────────────────────
KEYCLOAK_INTERNAL_URL = os.getenv("KEYCLOAK_INTERNAL_URL", "http://cosmic-keycloak:8080")
KEYCLOAK_PUBLIC_URL = os.getenv("KEYCLOAK_PUBLIC_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "cosmic")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_CLIENT_SECRET = os.getenv(
    "KEYCLOAK_CLIENT_SECRET"
)
OIDC_ISSUER = f"{KEYCLOAK_PUBLIC_URL}/realms/{KEYCLOAK_REALM}"

# ── Google ──────────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_AUTH_URL = os.getenv(
    "GOOGLE_AUTH_URL", "https://accounts.google.com/o/oauth2/v2/auth"
)
GOOGLE_TOKEN_URL = os.getenv(
    "GOOGLE_TOKEN_URL", "https://oauth2.googleapis.com/token"
)
GOOGLE_JWKS_URL = os.getenv(
    "GOOGLE_JWKS_URL", "https://www.googleapis.com/oauth2/v3/certs"
)
GOOGLE_ISSUER = os.getenv("GOOGLE_ISSUER", "https://accounts.google.com")