### Core modules ###
from fastapi import (
    APIRouter,
    HTTPException,
    status
)


### Type hints ###
from typing import Any
from ...cores.tags import APITag


### Internal modules ###
from ...interfaces.iams import IAMProviderDependency
from ...models.datas.roles import (
    RoleCreate,
    RoleUpdate
)
from ...models.responses.roles import (
    RoleCreateResponse,
    RoleDeleteResponse,
    RoleUpdateResponse
)


roles_v1_router: APIRouter = APIRouter(
    prefix="/api/v1/roles",
    tags=[APITag.role]
)


def _role_name(value: str, field: str = "name") -> str:
    name: str = value.strip()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "400 - Bad Request",
                "message": f"Field [{field}] cannot be empty."
            }
        )

    return name


@roles_v1_router.post(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=RoleCreateResponse
)
async def create_iam_role_v1(
    role:   RoleCreate,
    iam:    IAMProviderDependency
) -> Any:
    """Create/ensure a role in the IAM provider before the local DB write."""
    role_name: str = _role_name(value=role.name)

    await iam.create_role(
        name=role_name,
        desc=role.desc
    )

    return {
        "success": True,
        "created": {
            "name": role_name
        }
    }


@roles_v1_router.patch(
    path="/{role_name}",
    status_code=status.HTTP_200_OK,
    response_model=RoleUpdateResponse
)
async def update_iam_role_v1(
    role_name:  str,
    role:       RoleUpdate,
    iam:        IAMProviderDependency
) -> Any:
    """Rename/update a role in the IAM provider before the local DB write."""
    role_data: dict[str, Any] = role.model_dump(
        mode="json",
        exclude_unset=True
    )

    if not role_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "400 - Bad Request",
                "message": "Incoming data cannot be empty."
            }
        )

    new_name: str | None = None

    if "name" in role_data:
        if role_data["name"] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "400 - Bad Request",
                    "message": "Field [name] cannot be null."
                }
            )

        new_name = _role_name(value=str(role_data["name"]))

    new_desc: str | None = None

    if "desc" in role_data:
        # An explicit null clears the description. Keycloak stores it as an
        # empty string, which is equivalent for display purposes.
        new_desc = (
            str(role_data["desc"])
            if role_data["desc"] is not None
            else ""
        )

    await iam.update_role(
        current_name=role_name,
        name=new_name,
        desc=new_desc
    )

    return {
        "success": True,
        "updated": {
            "name": (
                new_name
                if new_name is not None
                else role_name
            )
        }
    }


@roles_v1_router.delete(
    path="/{role_name}",
    status_code=status.HTTP_200_OK,
    response_model=RoleDeleteResponse
)
async def delete_iam_role_v1(
    role_name:  str,
    iam:        IAMProviderDependency
) -> Any:
    """Delete an IAM role (idempotent when it is already gone)."""
    await iam.delete_role(name=role_name)

    return {
        "success": True,
        "deleted": {
            "name": role_name
        }
    }
