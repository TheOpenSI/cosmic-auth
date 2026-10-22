### Core modules ###
from datetime import (
    datetime,
    timezone
)
from uuid import uuid7
from fastapi import (
    HTTPException,
    status
)
from sqlmodel import select


### Type hints ###
from collections.abc import Collection


### Internal modules ###
from ..cores.configs import SYSTEM_ROLES
from ..cores.db import SessionDependency
from ..models.datas.claims import NormalisedClaims
from ..models.tables import (
    Roles,
    UserIdentities,
    Users
)


def _db_role(
    session: SessionDependency,
    name: str
) -> Roles:
    role: Roles | None = session.exec(
        statement=select(Roles).where(
            Roles.name.ilike(name)
        )
    ).first()

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "500 - Internal Server Error",
                "message": f"Default '{name}' role not found."
            }
        )

    return role


def _user_sync(
    user: Users,
    claims: NormalisedClaims,
    role: Roles
) -> None:
    """Mirror the Keycloak identity/role onto the local user row."""
    if claims.name:
        user.name = claims.name

    if claims.email:
        user.email = claims.email.strip().lower()

    if user.role_id != role.id:
        user.role_id = role.id


def platform_role(
    roles:          list[str],
    known_roles:    Collection[str] | None = None
) -> str:
    """Pick the CoSMIC platform role from Keycloak's realm roles."""
    normalised_roles: set[str] = {
        role.strip().lower()
        for role in roles
        if isinstance(role, str)
    }
    available_roles: set[str] = {
        role.strip().lower()
        for role in (known_roles or SYSTEM_ROLES)
        if (
            isinstance(role, str)
            and
            role.strip()
        )
    }

    # Admin always wins so a user carrying both a custom role and the composite
    # `admin` role keeps full access.
    if (
        "admin" in normalised_roles
        and
        "admin" in available_roles
    ):
        return "admin"

    # A custom role is an explicit assignment, so it takes precedence over the
    # default `user` role that Keycloak adds through `default-roles-cosmic`.
    for role in sorted(available_roles - set(SYSTEM_ROLES)):
        if role in normalised_roles:
            return role

    if (
        "user" in normalised_roles
        and
        "user" in available_roles
    ):
        return "user"

    for role in SYSTEM_ROLES:
        if (
            role in normalised_roles
            and
            role in available_roles
        ):
            return role

    return "user"


def normalise_claims_roles(
    claims:         NormalisedClaims,
    known_roles:    Collection[str] | None = None
) -> str:
    """
    Make sure the claim list always carries a platform role.

    Keycloak returns the realm roles on the access token, but users registered
    before the `user` default role was configured may have no CoSMIC role yet.
    Treating them as `user` keeps the current session on `/me` contract
    consistent.
    """
    role: str = platform_role(
        roles=claims.roles,
        known_roles=known_roles
    )
    existing_roles: set[str] = {
        role_name.strip().lower()
        for role_name in claims.roles
        if isinstance(role_name, str)
    }

    if role not in existing_roles:
        claims.roles.append(role)

    return role


def ensure_user(
    session:    SessionDependency,
    claims:     NormalisedClaims
) -> Users:
    if not claims.sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "400 - Bad Request",
                "message": "Login requires a stable subject (sub)."
            }
        )

    role: Roles = _db_role(
        session=session,
        name=normalise_claims_roles(
            claims=claims,
            known_roles={
                role_row.name
                for role_row in session.exec(
                    statement=select(Roles)
                ).all()
            }
        )
    )

    identity: UserIdentities | None = session.exec(
        statement=select(UserIdentities).where(
            UserIdentities.provider == claims.provider,
            UserIdentities.sub == claims.sub
        )
    ).first()

    if identity:
        user: Users | None = session.get(
            entity=Users,
            ident=identity.user_id
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "500 - Internal Server Error",
                    "message": "Identity points at missing user."
                }
            )

        _user_sync(
            user=user,
            claims=claims,
            role=role
        )

        session.add(instance=user)
        session.commit()
        session.refresh(instance=user)

        return user

    if not claims.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "400 - Bad Request",
                "message": "Login requires an email claim from the IdP."
            }
        )

    email: str = claims.email.strip().lower()

    user: Users | None = session.exec(
        statement=select(Users).where(
            Users.email.ilike(email)
        )
    ).first()

    if not user:
        user = Users(
            id=uuid7(),
            role_id=role.id,
            name=(
                claims.name
                or
                email
            ),
            email=email,
            create_on=datetime.now(tz=timezone.utc)
        )

        session.add(instance=user)
        session.flush()

    else:
        _user_sync(
            user=user,
            claims=claims,
            role=role
        )

    session.add(
        instance=UserIdentities(
            id=uuid7(),
            user_id=user.id,
            provider=claims.provider,
            sub=claims.sub,
            created_on=datetime.now(tz=timezone.utc)
        )
    )

    session.commit()
    session.refresh(instance=user)

    return user
