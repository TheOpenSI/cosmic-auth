# config.py - for the configuration for the backend to keycloak - fastapi-keycloak for redirecting the login to keycloak and getting the tokens/cookies for the frontend.


import os

KEYCLOAK_INTERNAL_URL = os.getenv("KEYCLOAK_INTERNAL_URL", "http://cosmic-keycloak:8080")
KEYCLOAK_PUBLIC_URL   = os.getenv("KEYCLOAK_PUBLIC_URL",   "http://localhost:8080")
KEYCLOAK_REALM        = os.getenv("KEYCLOAK_REALM",        "cosmic")
KEYCLOAK_CLIENT_ID    = os.getenv("KEYCLOAK_CLIENT_ID",    "cosmic-fastapi-keycloak")
KEYCLOAK_CLIENT_SECRET= os.getenv("KEYCLOAK_CLIENT_SECRET","cosmic-fastapi-keycloak-secret-dev")

AUTH_PUBLIC_URL = os.getenv("AUTH_PUBLIC_URL", "http://localhost:8081")
FRONTEND_URL    = os.getenv("FRONTEND_URL",    "http://localhost:5173")

AUTH_API_PREFIX = "/api/v1/auth"
AUTH_CALLBACK_URL = f"{AUTH_PUBLIC_URL}{AUTH_API_PREFIX}/callback"

ACCESS_TOKEN_COOKIE  = "cosmic_access_token"
REFRESH_TOKEN_COOKIE = "cosmic_refresh_token"
OAUTH_STATE_COOKIE   = "cosmic_oauth_state"

OIDC_ISSUER = f"{KEYCLOAK_PUBLIC_URL}/realms/{KEYCLOAK_REALM}"