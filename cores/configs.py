### Core modules ###
from pathlib import Path
from dotenv import dotenv_values


### Type hints ###


### Internal modules ###


def get_db_env() -> dict[str, str | None]:
    """Load `cores/cosmic_cfg.env` (shared database and application settings)."""
    env_file: Path = Path(__file__).resolve(strict=True).parent / "cosmic_cfg.env"

    return dotenv_values(
        dotenv_path=env_file,
        encoding="utf-8"
    )


def get_auth_env() -> dict[str, str | None]:
    """Load `cores/cosmic_auth.env` (BFF framework, session and Keycloak settings)."""
    env_file: Path = Path(__file__).resolve(strict=True).parent / "cosmic_auth.env"

    return dotenv_values(
        dotenv_path=env_file,
        encoding="utf-8"
    )


cosmic_db_configs: dict[str, str | None] = get_db_env()
cosmic_auth_configs: dict[str, str | None] = get_auth_env()


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


### IAM provider ###
IAM_PROVIDER: str | None = cosmic_auth_configs.get(
    "IAM_PROVIDER",
    "keycloak"
)
