"""
Django Ninja authentication backends for JWT token authentication.

This module provides authentication backends that can be used
with Django Ninja endpoints to secure specific APIs.
"""

from typing import Optional, Any, List
from ninja.security import HttpBearer
from django.http import HttpRequest
from functools import wraps
import logging
import django.utils.timezone
from asgiref.sync import sync_to_async

from dataportal.models import APIToken
from dataportal.authentication.utils import decode_jwt_token
from dataportal.authentication.roles import APIRoles
from dataportal.schema.response_schemas import ErrorCode
from dataportal.utils.errors import raise_http_error

logger = logging.getLogger(__name__)


class AuthenticatedUser:
    """
    Container for authenticated user information including roles.
    """

    def __init__(self, name: str, roles: List[str] = None):
        self.name = name
        self.roles = roles or []

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        # Admin has all roles
        if APIRoles.ADMIN in self.roles:
            return True
        return role in self.roles

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        if APIRoles.ADMIN in self.roles:
            return True
        return any(role in self.roles for role in roles)

    def has_all_roles(self, roles: List[str]) -> bool:
        """Check if user has all of the specified roles."""
        if APIRoles.ADMIN in self.roles:
            return True
        return all(role in self.roles for role in roles)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"AuthenticatedUser(name='{self.name}', roles={self.roles})"


class JWTAuth(HttpBearer):
    """
    JWT authentication for Django Ninja endpoints.

    This authentication class validates JWT tokens against the APIToken
    model in the database. It checks:
    1. Token format and JWT signature
    2. Token exists in database
    3. Token is active and not expired
    4. Updates last_used_at timestamp
    5. Extracts roles from token

    Usage:
        from dataportal.authentication import JWTAuth
        from ninja import Router

        router = Router()
        jwt_auth = JWTAuth()

        @router.get("/protected", auth=jwt_auth)
        def protected_endpoint(request):
            user = request.auth  # AuthenticatedUser object
            return {"message": f"Hello {user.name}!", "roles": user.roles}
    """

    async def authenticate(self, request: HttpRequest, token: str) -> Optional[AuthenticatedUser]:
        """
        Authenticate the request using JWT token.

        Args:
            request: Django HTTP request object
            token: JWT token string from Authorization header

        Returns:
            AuthenticatedUser object if authenticated, None otherwise
        """
        logger.debug("[JWT Auth] Starting authentication")
        logger.debug(
            f"[JWT Auth] Token preview: {token[:20]}...{token[-20:] if len(token) > 40 else ''}"
        )

        # Decode and validate JWT token
        payload = decode_jwt_token(token)
        if not payload:
            logger.warning("[JWT Auth] Failed to decode JWT token - invalid signature or format")
            return None

        logger.debug(f"[JWT Auth] Token decoded successfully. Subject: {payload.get('sub')}")

        # Validate issuer and audience (prevent token misuse)
        if payload.get("iss") and payload.get("iss") != "mett-dataportal":
            logger.warning(
                f"[JWT Auth] Invalid issuer: {payload.get('iss')} (expected: mett-dataportal)"
            )
            return None  # Wrong issuer

        if payload.get("aud") and payload.get("aud") != "mett-dataportal-api":
            logger.warning(
                f"[JWT Auth] Invalid audience: {payload.get('aud')} (expected: mett-dataportal-api)"
            )
            return None  # Wrong audience

        # Extract user name from token
        name = payload.get("sub")
        if not name:
            logger.warning("[JWT Auth] No subject (sub) found in token payload")
            return None

        logger.debug(
            f"[JWT Auth] Token validation passed. Looking up token in database for user: {name}"
        )

        # Extract roles from token (if present)
        roles_from_jwt = payload.get("roles", [])
        logger.debug(f"[JWT Auth] Roles in JWT payload: {roles_from_jwt}")

        # Check if token exists in database and is valid
        # Use sync_to_async for all database operations
        try:
            # Database query - wrapped with sync_to_async
            @sync_to_async
            def get_token():
                return APIToken.objects.select_related().prefetch_related("roles").get(token=token)

            api_token = await get_token()
            logger.debug(
                f"[JWT Auth] Token found in database (ID: {api_token.pk}, Name: {api_token.name})"
            )

            @sync_to_async
            def check_token_valid():
                return api_token.is_valid()

            if not await check_token_valid():
                # Token is inactive or expired
                @sync_to_async
                def get_token_status():
                    return api_token.is_active, api_token.is_expired()

                is_active, is_expired = await get_token_status()
                logger.warning(
                    f"[JWT Auth] Token is invalid - "
                    f"Active: {is_active}, "
                    f"Expired: {is_expired}"
                )
                return None

            logger.debug("[JWT Auth] Token is valid and active")

            # Get roles from database (many-to-many relationship)
            @sync_to_async
            def get_roles():
                return list(api_token.roles.filter(is_active=True).values_list("code", flat=True))

            roles = await get_roles()
            logger.debug(f"[JWT Auth] Roles from database M2M: {roles}")

            if not roles and roles_from_jwt:
                logger.warning(
                    f"[JWT Auth] Token has roles in JWT ({roles_from_jwt}) but none in database M2M. "
                    f"M2M relationship may not be set up correctly."
                )

            # Update last used timestamp in a non-blocking way
            @sync_to_async
            def update_last_used():
                APIToken.objects.filter(pk=api_token.pk).update(
                    last_used_at=django.utils.timezone.now()
                )

            await update_last_used()

            # Return AuthenticatedUser object
            user = AuthenticatedUser(name=name, roles=roles)
            logger.info(
                f"[JWT Auth] ✅ Authentication successful for '{name}' "
                f"(token_id={api_token.pk}, roles={len(roles)})"
            )
            return user

        except APIToken.DoesNotExist:
            # Token not found in database
            logger.warning(f"[JWT Auth] Token not found in database for user: {name}")
            return None
        except Exception as e:
            # Any other error
            logger.error(
                f"[JWT Auth] Unexpected error during authentication: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            return None


class RoleBasedJWTAuth(JWTAuth):
    """
    Role-based JWT authentication for Django Ninja endpoints.

    This class extends JWTAuth to also check if the authenticated user
    has specific roles required for the endpoint.

    Usage:
        from dataportal.authentication import RoleBasedJWTAuth
        from dataportal.authentication.roles import APIRoles
        from ninja import Router

        router = Router()
        proteomics_auth = RoleBasedJWTAuth(required_roles=[APIRoles.PROTEOMICS])

        @router.get("/proteomics-data", auth=proteomics_auth)
        def get_proteomics_data(request):
            return {"data": "proteomics"}
    """

    def __init__(self, required_roles: List[str] = None, require_all: bool = False):
        """
        Initialize role-based authentication.

        Args:
            required_roles: List of roles required to access the endpoint
            require_all: If True, user must have ALL roles; if False, ANY role is sufficient
        """
        super().__init__()
        self.required_roles = required_roles or []
        self.require_all = require_all

    async def authenticate(self, request: HttpRequest, token: str) -> Optional[AuthenticatedUser]:
        """
        Authenticate and check roles.

        Args:
            request: Django HTTP request object
            token: JWT token string from Authorization header

        Returns:
            AuthenticatedUser if authenticated and has required roles, None otherwise
        """
        # First, perform standard authentication
        user = await super().authenticate(request, token)

        if not user:
            return None

        # If no roles required, return user
        if not self.required_roles:
            return user

        # Check if user has required roles
        if self.require_all:
            # User must have all required roles
            if not user.has_all_roles(self.required_roles):
                return None
        else:
            # User must have at least one required role
            if not user.has_any_role(self.required_roles):
                return None

        return user


class OptionalJWTAuth(JWTAuth):
    """
    Optional JWT authentication for Django Ninja endpoints.

    This is a variant that allows both authenticated and unauthenticated access.
    If a valid token is provided, the user is authenticated.
    If no token or invalid token is provided, the request proceeds as anonymous.

    Usage:
        from dataportal.authentication import OptionalJWTAuth
        from ninja import Router

        router = Router()
        optional_auth = OptionalJWTAuth()

        @router.get("/semi-protected", auth=optional_auth)
        def semi_protected_endpoint(request):
            if request.auth:
                return {"message": f"Hello, {request.auth.name}!"}
            else:
                return {"message": "Hello, anonymous!"}
    """

    async def authenticate(self, request: HttpRequest, token: str) -> Optional[Any]:
        """
        Authenticate if token is provided, otherwise allow anonymous access.

        Args:
            request: Django HTTP request object
            token: JWT token string from Authorization header (or None)

        Returns:
            AuthenticatedUser if authenticated, None for anonymous
        """
        if not token:
            return None  # Allow anonymous access

        result = await super().authenticate(request, token)
        return result if result else None  # Allow anonymous if token invalid


# Singleton instances for convenience
jwt_auth = JWTAuth()
optional_jwt_auth = OptionalJWTAuth()

# Convenience instances for common role requirements
proteomics_auth = RoleBasedJWTAuth(required_roles=[APIRoles.PROTEOMICS])
essentiality_auth = RoleBasedJWTAuth(required_roles=[APIRoles.ESSENTIALITY])
fitness_auth = RoleBasedJWTAuth(required_roles=[APIRoles.FITNESS])
experimental_data_auth = RoleBasedJWTAuth(
    required_roles=[APIRoles.PROTEOMICS, APIRoles.ESSENTIALITY, APIRoles.FITNESS]
)


def get_authenticated_user(request: HttpRequest) -> Optional[AuthenticatedUser]:
    """
    Helper function to get the authenticated user from request.

    This can be used within endpoint functions to access the authenticated user.

    Args:
        request: Django HTTP request object

    Returns:
        AuthenticatedUser if authenticated via JWT, None otherwise

    Example:
        @router.get("/my-endpoint", auth=jwt_auth)
        def my_endpoint(request):
            user = get_authenticated_user(request)
            return {"user": user.name, "roles": user.roles}
    """
    # The authenticated value is set by Ninja's auth system
    # and is available as request.auth
    return getattr(request, "auth", None)


def require_role(role: str):
    """
    Decorator to check if authenticated user has a specific role.
    Use this in addition to auth parameter on the endpoint.

    Args:
        role: Required role name

    Example:
        @router.get("/proteomics", auth=jwt_auth)
        @require_role(APIRoles.PROTEOMICS)
        def get_proteomics(request):
            return {"data": "proteomics"}
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            user = get_authenticated_user(request)
            if not user or not user.has_role(role):
                raise_http_error(
                    status_code=403,
                    message=f"Access denied: '{role}' role required",
                    error_code=ErrorCode.FORBIDDEN,
                )
            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_any_role(*roles):
    """
    Decorator to check if authenticated user has any of the specified roles.

    Args:
        *roles: Role names (one or more)

    Example:
        @router.get("/experimental", auth=jwt_auth)
        @require_any_role(APIRoles.PROTEOMICS, APIRoles.ESSENTIALITY)
        def get_experimental(request):
            return {"data": "experimental"}
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            user = get_authenticated_user(request)
            if not user or not user.has_any_role(list(roles)):
                raise_http_error(
                    status_code=403,
                    message=f"Access denied: one of {list(roles)} roles required",
                    error_code=ErrorCode.FORBIDDEN,
                )
            return func(request, *args, **kwargs)

        return wrapper

    return decorator
