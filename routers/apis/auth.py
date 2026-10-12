### Core modules ###
from httpx import HTTPError
from authlib.integrations.base_client import OAuthError
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse
)


### Type hints ###
from typing import Any
from uuid import UUID
from ...cores.tags import APITag


### Internal modules ###
from ...cores.configs import FRONTEND_URL
from ...utils.keys import jwk_set
from ...utils.session import (
    clear_auth_cookies,
    read_current_session,
    read_expired_session,
    set_session_cookie,
    unauthorised_cleared
)
from ...models.datas.claims import NormalisedClaims
from ...models.tables import Users
from ...interfaces.iams import IAMProviderDependency
from ...utils.users_sync import ensure_user
from ...cores.db import SessionDependency


auth_v1_router: APIRouter = APIRouter(
    prefix="/api/v1/auth",
    tags=[APITag.auth]
)


_ALREADY_SIGNED_IN_TEMPLATE: str = """
    <!DOCTYPE html>

    <html lang="en">
        <head>
            <meta charset="utf-8" />
            <title>Already signed in</title>
        </head>

        <body style="font-family: sans-serif; padding: 2rem;">
            <h1>Already signed in</h1>
            <p>You can close this tab and continue in the other window.</p>

            <script>
                setTimeout(
                    () => { window.close();},
                    3000,
                );
            </script>
        </body>
    </html>
"""


# Google & Microsoft are brokered inside Keycloak, so there is no direct-to-IdP
# path to expose even if an old bookmark still points at one.
_LOGIN_PATH: str = "/api/v1/auth/login"


@auth_v1_router.get(
    path="/jwks.json",
    status_code=status.HTTP_200_OK
)
async def jwks() -> dict[str, list[dict[str, str | list[str]]]]:
    """Public JWKS so the other CoSMIC microservices can verify the session."""
    return jwk_set()


@auth_v1_router.get(
    path="/login",
    status_code=status.HTTP_200_OK
)
async def login(
    request:    Request,
    iam:        IAMProviderDependency
) -> RedirectResponse:
    return await iam.authorize_redirect(
        request=request,
        redirect_uri=iam.callback_url()
    )


@auth_v1_router.get(
    path="/login/{provider}",
    status_code=status.HTTP_200_OK
)
async def login_provider(
    request:    Request,
    provider:   str,
    iam:        IAMProviderDependency
) -> RedirectResponse:
    if provider.strip().lower() != iam.name:
        return RedirectResponse(
            url=_LOGIN_PATH,
            status_code=status.HTTP_302_FOUND
        )

    return await iam.authorize_redirect(
        request=request,
        redirect_uri=iam.callback_url()
    )


@auth_v1_router.get(
    path="/callback/{provider}",
    status_code=status.HTTP_200_OK
)
async def callback_provider(
    provider:   str,
    request:    Request,
    session:    SessionDependency,
    iam:        IAMProviderDependency,
    code:       str | None = None,
    state:      str | None = None,
    error:      str | None = None
) -> Response:
    if provider.strip().lower() != iam.name:
        return RedirectResponse(
            url=_LOGIN_PATH,
            status_code=status.HTTP_302_FOUND
        )

    try:
        read_current_session(request=request)

        # Already logged in, avoid a double callback.
        return HTMLResponse(
            content=_ALREADY_SIGNED_IN_TEMPLATE,
            status_code=status.HTTP_200_OK
        )

    except HTTPException:
        pass

    if error:
        return RedirectResponse(
            url=f"{str(FRONTEND_URL)}/login?error={error}",
            status_code=status.HTTP_302_FOUND
        )

    if (
        not code
        or
        not state
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OAuth code or state"
        )

    try:
        tokens: dict[str, Any] = await iam.exchange_code(request=request)

        claims: NormalisedClaims = iam.claims_from_user_info(
            user_info=tokens.get(
                "userinfo",
                {}
            )
        )

        user: Users = ensure_user(
            session=session,
            claims=claims
        )

        # Keep the ID token so logout can use RP-initiated logout.
        request.session["id_token"] = tokens.get(
            "id_token",
            None
        )

        response: RedirectResponse = RedirectResponse(
            url=f"{str(FRONTEND_URL)}/chat",
            status_code=status.HTTP_302_FOUND
        )

        # CoSMIC session is the single source of truth for `/me`, `/refresh` &
        # `/logout` endpoints. The Keycloak refresh token travels inside the JWT
        # token
        set_session_cookie(
            response=response,
            claims=claims,
            user_id=user.id,
            refresh_token=tokens.get(
                "refresh_token",
                None
            ),
            max_age=tokens.get(
                "refresh_expires_in",
                None
            )
        )

        return response

    except OAuthError as oauth_exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "400 - Bad Request",
                "message": f"OAuth callback failed: {oauth_exc.error}."
            }
        )


@auth_v1_router.post(
    path="/logout",
    status_code=status.HTTP_200_OK
)
async def logout(
    request:    Request,
    iam:        IAMProviderDependency
) -> RedirectResponse:
    refresh_token: str | None = None

    try:
        old_session_token: dict[str, str | list[str] | None] = read_expired_session(request=request)
        stored_refresh_token: str | list[str] | None = old_session_token.get(
            "refresh_token",
            None
        )
        refresh_token: str | list[str] | None = (
            stored_refresh_token
            if   (isinstance(stored_refresh_token, str))
            else (None)
        )

    except HTTPException as fastapi_exc:
        refresh_token = None

    if refresh_token:
        try:
            await iam.revoke(refresh_token=refresh_token)

        except Exception:  # noqa: BLE001 - logout must never trap the user
            pass

    id_token: str | None = request.session.pop(
        "id_token",
        None
    )

    response: RedirectResponse = RedirectResponse(
        url=iam.logout_redirect(
            post_logout_redirect_uri=f"{str(FRONTEND_URL)}/login",
            id_token=id_token
        ),
        status_code=status.HTTP_302_FOUND
    )

    clear_auth_cookies(response=response)

    return response


@auth_v1_router.post(
    path="/refresh",
    status_code=status.HTTP_200_OK
)
async def refresh(
    request:    Request,
    session:    SessionDependency,
    iam:        IAMProviderDependency
) -> JSONResponse:
    old_session_token: dict[str, str | list[str] | None] = read_expired_session(request=request)
    stored_refresh_token: str | list[str] | None = old_session_token.get(
        "refresh_token",
        None
    )
    refresh_token: str | list[str] | None = (
        stored_refresh_token
        if   (isinstance(stored_refresh_token, str))
        else (None)
    )

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "401 - Unauthorized",
                "message": "No refresh token in session."
            }
        )

    # Guard against case when session JWT is signed but never index blindly
    stored_user_id: str | list[str] | None = old_session_token.get(
        "user_id",
        None
    )

    if not isinstance(stored_user_id, str):
        return unauthorised_cleared()

    user_id: UUID = UUID(stored_user_id)

    if session.get(
        entity=Users,
        ident=user_id
    ) is None:
        return unauthorised_cleared()

    try:
        tokens: dict[str, Any]          = await iam.refresh(refresh_token=refresh_token)
        claims: NormalisedClaims | None = None

        if tokens.get(
            "id_token",
            None
        ):
            try:
                user_info: dict[str, Any] = await iam.parse_id_token(tokens=tokens)

                claims = iam.claims_from_user_info(user_info=user_info)

            except Exception:  # noqa: BLE001 - fall back to the current session
                claims = None

        if (
            claims is None
            or
            not claims.sub
        ):
            claims = NormalisedClaims(
                provider=old_session_token.get(
                    "provider",
                    "keycloak"
                ),
                sub=old_session_token.get(
                    "sub",
                    None
                ),
                email=old_session_token.get(
                    "email",
                    None
                ),
                name=old_session_token.get(
                    "name",
                    None
                ),
                roles=old_session_token.get(
                    "roles",
                    []
                )
            )

        new_refresh: str | None = tokens.get(
            "refresh_token",
            refresh_token
        )

        # Use single response object only for cookie AND return body
        response: JSONResponse = JSONResponse({"ok": True})

        set_session_cookie(
            response=response,
            claims=claims,
            user_id=user_id,
            refresh_token=new_refresh,
            max_age=tokens.get(
                "refresh_expires_in",
                None
            )
        )

        return response

    except (
        OAuthError,
        HTTPError
    ) as refresh_exc: # noqa: BLE001 - surface as a 401 to the client
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "401 - Unauthorized",
                "message": "Token refresh failed."
            }
        ) from refresh_exc

    except Exception as python_exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "500 - Internal Server Error",
                "message": f"Error: {python_exc}"
                }
        )


@auth_v1_router.get(
    path="/me",
    status_code=status.HTTP_200_OK
)
async def me(
    request: Request,
    session: SessionDependency
) -> JSONResponse:
    payload: dict[str, str | list[str] | None] = read_current_session(request=request)
    user_id: str | list[str] | None = payload.get(
        "user_id",
        None
    )

    if (
        not user_id
        or session.get(
            entity=Users,
            ident=UUID(str(user_id))
        ) is None
    ):
        return unauthorised_cleared()

    return JSONResponse(
        {
            "user_id": payload.get(
                "user_id",
                None
            ),
            "sub": payload.get(
                "sub",
                None
            ),
            "email": payload.get(
                "email",
                None
            ),
            "name": payload.get(
                "name",
                None
            ),
            "roles": payload.get(
                "roles",
                []
            ),
            "provider": payload.get(
                "provider",
                None
            )
        }
    )
