"""
Django Ninja authentication backends for JWT token authentication.

This module provides authentication backends that can be used
with Django Ninja endpoints to secure specific APIs.
"""

from typing import Optional, Any, List
from ninja.security import HttpBearer
from django.http import HttpRequest
from functools import wraps

from dataportal.models import APIToken
from dataportal.authentication.utils import decode_jwt_token, extract_token_from_header
from dataportal.authentication.roles import APIRoles


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
    
    def authenticate(self, request: HttpRequest, token: str) -> Optional[AuthenticatedUser]:
        """
        Authenticate the request using JWT token.
        
        Args:
            request: Django HTTP request object
            token: JWT token string from Authorization header
            
        Returns:
            AuthenticatedUser object if authenticated, None otherwise
        """
        # Decode and validate JWT token
        payload = decode_jwt_token(token)
        if not payload:
            return None
        
        # Validate issuer and audience (prevent token misuse)
        if payload.get("iss") and payload.get("iss") != "mett-dataportal":
            return None  # Wrong issuer
        
        if payload.get("aud") and payload.get("aud") != "mett-dataportal-api":
            return None  # Wrong audience
        
        # Extract user name from token
        name = payload.get("sub")
        if not name:
            return None
        
        # Extract roles from token (if present)
        roles = payload.get("roles", [])
        
        # Check if token exists in database and is valid
        try:
            api_token = APIToken.objects.get(token=token)
            
            if not api_token.is_valid():
                # Token is inactive or expired
                return None
            
            # Update last used timestamp (async to avoid blocking)
            api_token.mark_as_used()
            
            # Get roles from database (many-to-many relationship)
            roles = api_token.get_role_codes()
            
            # Return AuthenticatedUser object
            return AuthenticatedUser(name=name, roles=roles)
            
        except APIToken.DoesNotExist:
            # Token not found in database
            return None
        except Exception:
            # Any other error
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
    
    def authenticate(self, request: HttpRequest, token: str) -> Optional[AuthenticatedUser]:
        """
        Authenticate and check roles.
        
        Args:
            request: Django HTTP request object
            token: JWT token string from Authorization header
            
        Returns:
            AuthenticatedUser if authenticated and has required roles, None otherwise
        """
        # First, perform standard authentication
        user = super().authenticate(request, token)
        
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
    
    def authenticate(self, request: HttpRequest, token: str) -> Optional[Any]:
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
        
        result = super().authenticate(request, token)
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
                from ninja.errors import HttpError
                raise HttpError(403, f"Access denied: '{role}' role required")
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
                from ninja.errors import HttpError
                raise HttpError(403, f"Access denied: one of {list(roles)} roles required")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

