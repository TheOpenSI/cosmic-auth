### Core modules ###
from pathlib import Path
from dotenv import dotenv_values


### Type hints ###


### Internal modules ###


def get_db_env() -> dict[str, str | None]:
    """Load `cores/cosmic_cfg.env` (shared database and application settings)."""
    env_file: Path = Path(__file__).resolve(strict=True).parent.joinpath(
        "cosmic_cfg.env"
    )

    return dotenv_values(
        dotenv_path=env_file,
        encoding="utf-8"
    )


def get_auth_env() -> dict[str, str | None]:
    """Load `cores/cosmic_auth.env` (BFF framework, session and Keycloak settings)."""
    env_file: Path = Path(__file__).resolve(strict=True).parent.joinpath(
        "cosmic_auth.env"
    )

    return dotenv_values(
        dotenv_path=env_file,
        encoding="utf-8"
    )


def read_secret(name: str) -> str | None:
    """
    Read a value from `docker/secrets/<name>.txt`.

    The Keycloak service-account secret is stored next to the other Keycloak
    secrets already used by this micro-service. Keeping the file as the fallback
    means a native or Docker checkout works without duplicating the secret in
    `cosmic_auth.env`, while the env variable can still override it.
    """
    secret_file: Path = Path(__file__).resolve().parent.parent.joinpath(
        "docker",
        "secrets",
        f"{name}.txt"
    )

    if not secret_file.is_file():
        return None

    value: str = secret_file.read_text(encoding="utf-8").strip()

    return (
        value
        or
        None
    )


cosmic_db_configs:      dict[str, str | None] = get_db_env()
cosmic_auth_configs:    dict[str, str | None] = get_auth_env()


### BFF Framework ###
AUTH_PUBLIC_URL: str | None = cosmic_auth_configs.get(
    "AUTH_PUBLIC_URL",
    "http://localhost:8081"
)
FRONTEND_URL: str | None = cosmic_auth_configs.get(
    "FRONTEND_URL",
    "http://localhost:5173"
)


### CoSMIC session ###
SESSION_COOKIE_NAME: str | None = cosmic_auth_configs.get(
    "SESSION_COOKIE_NAME",
    "cosmic_session"
)
SESSION_MAX_AGE: int = int(
    cosmic_auth_configs.get("SESSION_MAX_AGE")
    or
    "900"
)
SESSION_REFRESH_TOKEN_MAX_AGE: int = int(
    cosmic_auth_configs.get("SESSION_REFRESH_TOKEN_MAX_AGE")
    or
    "86400"
)
SESSION_ISSUER: str | None = cosmic_auth_configs.get(
    "SESSION_ISSUER",
    "cosmic-auth"
)
SESSION_PRIVATE_KEY_PATH: Path | None = Path(
    cosmic_auth_configs.get("SESSION_PRIVATE_KEY_PATH")
    or
    Path(__file__).resolve().parent.parent.joinpath(
        "docker",
        "secrets",
        "cosmic_private_session.pem"
    )
)
SESSION_PUBLIC_KEY_PATH: Path = Path(
    cosmic_auth_configs.get("SESSION_PUBLIC_KEY_PATH")
    or
    Path(__file__).resolve().parent.parent.joinpath(
        "docker",
        "secrets",
        "cosmic_public_session.pem"
    )
)
SESSION_KEY_ID: str | None = cosmic_auth_configs.get(
    "SESSION_KEY_ID",
    None
)


### Starlette SessionMiddleware (holds temporary Authlib OAuth state/nonce) ###
SESSION_SECRET: str | None = cosmic_auth_configs.get(
    "SESSION_SECRET",
    None
)
SESSION_OAUTH_COOKIE: str | None = cosmic_auth_configs.get(
    "OAUTH_SESSION_COOKIE",
    "cosmic_oauth_session"
)


### Keycloak (Google & Microsoft IdPs are integrated by default) ###
KEYCLOAK_INTERNAL_URL: str | None = cosmic_auth_configs.get(
    "KEYCLOAK_INTERNAL_URL",
    "http://cosmic-keycloak:8080"
)
KEYCLOAK_PUBLIC_URL: str | None = cosmic_auth_configs.get(
    "KEYCLOAK_PUBLIC_URL",
    "http://localhost:8080"
)
KEYCLOAK_REALM: str | None = cosmic_auth_configs.get(
    "KEYCLOAK_REALM",
    "cosmic"
)
KEYCLOAK_CLIENT_ID: str | None = cosmic_auth_configs.get(
    "KEYCLOAK_CLIENT_ID",
    None
)
KEYCLOAK_CLIENT_SECRET: str | None = cosmic_auth_configs.get(
    "KEYCLOAK_CLIENT_SECRET",
    None
)
# Dedicated confidential client used for Keycloak Admin REST calls. It is
# defined in `docker/keycloak/cosmic-realm.json` with a service account carrying
# the `realm-management` roles it needs (`manage-users`, `view-users`,
# `query-users`, `manage-realm`, `view-realm`).
KEYCLOAK_SERVICE_ACCOUNT_CLIENT_ID: str | None = cosmic_auth_configs.get(
    "KEYCLOAK_SERVICE_ACCOUNT_CLIENT_ID",
    "cosmic-auth-service"
)
KEYCLOAK_SERVICE_ACCOUNT_CLIENT_SECRET: str | None = (
    cosmic_auth_configs.get(
        "KEYCLOAK_SERVICE_ACCOUNT_CLIENT_SECRET",
        None
    )
    or
    read_secret("keycloak_service_account_client_secret")
)


### IAM provider ###
IAM_PROVIDER: str | None = cosmic_auth_configs.get(
    "IAM_PROVIDER",
    "keycloak"
)


### Other configs ###
SYSTEM_ROLES: tuple[str, ...] = (
    "admin",
    "user"
)
ALLOWED_ORIGINS: tuple[str, ...] = (
    str(FRONTEND_URL),
)
ALLOWED_METHODS: tuple[str, ...] = (
    "GET",
    "POST",
    "PATCH",
    "DELETE"
)
ALLOWED_HEADERS: tuple[str, ...] = (
    "*",
)
