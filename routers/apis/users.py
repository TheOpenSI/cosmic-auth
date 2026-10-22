### Core modules ###
from fastapi import (
    APIRouter,
    HTTPException,
    status
)
from uuid import UUID
from sqlmodel import select


### Type hints ###
from typing import Any
from ...cores.tags import APITag
from pydantic.types import UUID7


### Internal modules ###
from ...cores.db import SessionDependency
from ...interfaces.iams import IAMProviderDependency
from ...models.datas.users import UserUpdate
from ...models.responses.users import (
    UserDeleteResponse,
    UserUpdateResponse
)
from ...models.tables import (
    Roles,
    UserIdentities,
    Users
)


users_v1_router: APIRouter = APIRouter(
    prefix="/api/v1/users",
    tags=[APITag.user]
)


def _user_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "status": "404 - Not Found",
            "message": "User Not Found!"
        }
    )


@users_v1_router.patch(
    path="/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserUpdateResponse
)
async def update_iam_user_v1(
    user_id:    UUID7,
    user:       UserUpdate,
    session:    SessionDependency,
    iam:        IAMProviderDependency
) -> Any:
    """Push a user update to the IAM provider (the local DB is synced by `cosmic-db`)."""
    user_db: Users | None = session.get(
        entity=Users,
        ident=user_id
    )

    if user_db is None:
        raise _user_not_found()

    user_data: dict[str, Any] = user.model_dump(
        mode="json",
        exclude_unset=True
    )

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "400 - Bad Request",
                "message": "Incoming data cannot be empty."
            }
        )

    for field in (
        "role_id",
        "name",
        "email"
    ):
        if field in user_data and user_data[field] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "400 - Bad Request",
                    "message": f"Field [{field}] cannot be null."
                }
            )

    identity: UserIdentities | None = session.exec(
        statement=select(UserIdentities).where(
            UserIdentities.user_id == user_db.id,
            UserIdentities.provider == iam.name
        )
    ).first()

    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": "409 - Conflict",
                "message": "This user is not linked to the IAM provider."
            }
        )

    role_name: str | None = None
    role_desc: str | None = None

    if "role_id" in user_data:
        role: Roles | None = session.get(
            entity=Roles,
            ident=UUID(str(user_data["role_id"]))
        )

        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "404 - Not Found",
                    "message": "Role Not Found!"
                }
            )

        role_name = role.name
        role_desc = role.desc

    managed_roles: set[str] = {
        role_row.name
        for role_row in session.exec(statement=select(Roles)).all()
    }

    await iam.update_user(
        subject=identity.sub,
        email=(
            str(user_data["email"])
            if "email" in user_data
            else None
        ),
        name=(
            str(user_data["name"])
            if "name" in user_data
            else None
        ),
        role=role_name,
        role_desc=role_desc,
        managed_roles=managed_roles
    )

    return {
        "success": True,
        "updated": {
            "user_id": str(user_db.id),
            "iam_user_id": identity.sub
        }
    }


@users_v1_router.delete(
    path="/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserDeleteResponse
)
async def delete_iam_user_v1(
    user_id:    UUID7,
    session:    SessionDependency,
    iam:        IAMProviderDependency
) -> Any:
    """Delete the IAM-backed user (the local row is removed by `cosmic-db`)."""
    user_db: Users | None = session.get(
        entity=Users,
        ident=user_id
    )

    if user_db is None:
        raise _user_not_found()

    identity: UserIdentities | None = session.exec(
        statement=select(UserIdentities).where(
            UserIdentities.user_id == user_db.id,
            UserIdentities.provider == iam.name
        )
    ).first()

    # A legacy/local-only user has nothing to remove in the IAM. `cosmic-db`
    # still clears the fallback row so admins can clean it up.
    if identity is not None:
        await iam.delete_user(subject=identity.sub)

    return {
        "success": True,
        "deleted": {
            "user_id": str(user_db.id),
            "iam_user_id":  (
                identity.sub
                if identity is not None
                else None
            )
        }
    }
