from typing import Callable, Optional
import uuid
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import (
    AccountSuspendedError,
    AuthenticationError,
    AuthorizationError,
)
from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import AccountStatus, UserRole
from app.models.user import User
from app.repositories.user_repo import UserRepository

logger = get_logger("app.api.dependencies")
bearer_scheme = HTTPBearer(auto_error=False)
user_repo = UserRepository()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Authenticate request via bearer token and load current user from database.
    Never relies on client-provided claims for authorization state.
    """
    if not credentials or not credentials.credentials:
        raise AuthenticationError("Authorization header with Bearer token is required.")

    token = credentials.credentials
    payload = decode_access_token(token)

    sub = payload.get("sub")
    if not sub:
        raise AuthenticationError("Invalid token: Subject (sub) claim missing.")

    try:
        user_id = uuid.UUID(sub)
    except (ValueError, TypeError):
        raise AuthenticationError("Invalid token: Subject is not a valid UUID.")

    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise AuthenticationError("User associated with this token no longer exists.")

    if user.account_status == AccountStatus.SUSPENDED:
        logger.warning(f"Access attempted by suspended user {user.id}")
        raise AccountSuspendedError("Account is suspended. Access denied.")

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Ensure the authenticated user account is in ACTIVE status."""
    if user.account_status != AccountStatus.ACTIVE:
        raise AuthorizationError(
            f"Account status is '{user.account_status.value}'. Active status required."
        )
    return user


def require_role(*allowed_roles: UserRole) -> Callable:
    """
    Factory creating a dependency that enforces authorized user roles.
    Role is strictly loaded from the authoritative database record.
    """

    async def role_checker(user: User = Depends(get_current_active_user)) -> User:
        if user.role not in allowed_roles:
            logger.warning(
                f"Unauthorized role access attempt: user {user.id} (role={user.role.value}) "
                f"attempted to access endpoint requiring {[r.value for r in allowed_roles]}"
            )
            raise AuthorizationError(
                f"Access forbidden: Insufficient permissions for role '{user.role.value}'."
            )
        return user

    return role_checker


# Convenience role dependencies
require_customer = require_role(UserRole.CUSTOMER, UserRole.ADMIN)
require_brand_owner = require_role(UserRole.BRAND_OWNER, UserRole.ADMIN)
require_admin = require_role(UserRole.ADMIN)
