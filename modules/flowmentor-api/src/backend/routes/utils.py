from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from typing import Annotated
from pydantic import BaseModel

from ..utils import auth, log
from .. import conf
from ..clients.database import DatabaseClient

logger = log.get_logger(__name__)

#### Auth ####


class InvalidPrincipalException(HTTPException):
    def __init__(self, detail="Invalid principal"):
        super().__init__(
            status_code=401,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class PrincipalInfo(BaseModel):
    """Principal information."""

    # Add more fields here as needed - populate from claims
    claims: dict[str, str] = {}


def get_auth_client(app: FastAPI = Depends()):
    return app.state.auth_client


AuthClient = Annotated[auth.AuthClient, Depends(get_auth_client)]

http_bearer = HTTPBearer()


def get_request_principal(
    token: Annotated[str, Depends(http_bearer)],
    auth_client: AuthClient,
) -> PrincipalInfo:
    """Extracts principal info from the request token."""

    if auth_client:
        if not token or not token.credentials:
            raise InvalidPrincipalException()
        try:
            claims = auth_client.decode_token(token.credentials)
            return PrincipalInfo(claims=claims)
        except Exception as e:
            logger.warning(f"Failed to decode token: {e}")
            raise InvalidPrincipalException()
    else:
        return PrincipalInfo(claims={})


RequestPrincipal = Annotated[PrincipalInfo, Depends(get_request_principal)]

# NOTE: Implement variants on RequestPrincipal with constraints as needed, e.g.:
#
# def get_user_request_principal(
#     principal: Annotated[PrincipalInfo, Depends(get_request_principal)],
# ) -> PrincipalInfo:
#     if principal.claims.get("role") != "user":
#         raise InvalidPrincipalException(detail="Principal is not a user")
#     return principal
#
# UserRequestPrincipal = Annotated[PrincipalInfo, Depends(get_user_request_principal)]

#### Database ####


def get_database_client(request: Request):
    """
    FastAPI dependency that provides the PostgreSQL database client.

    Usage in routes:
        from .utils import DatabaseDB

        @router.post("/users")
        async def create_user(user: User, db: DatabaseDB):
            await db.upsert_user_profile(user_id, user.dict())
    """
    if not hasattr(request.app.state, "db_client"):
        raise HTTPException(
            status_code=503,
            detail="Database client is not configured.",
        )

    return request.app.state.db_client


# Type alias for dependency injection
DatabaseDB = Annotated["DatabaseClient", Depends(get_database_client)]
