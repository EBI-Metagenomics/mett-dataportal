"""
Authentication package for METT Data Portal.

This package provides JWT-based authentication with role-based access control
for Django Ninja API endpoints.

Main exports:
    - Authentication backends: JWTAuth, RoleBasedJWTAuth, OptionalJWTAuth
    - Pre-configured instances: jwt_auth, proteomics_auth, essentiality_auth, etc.
    - User class: AuthenticatedUser
    - Helper functions: get_authenticated_user, require_role, require_any_role
    - Roles: APIRoles, RolePresets
    - JWT utilities: generate_jwt_token, decode_jwt_token

Usage:
    from dataportal.authentication import jwt_auth, APIRoles
    
    @router.get("/protected", auth=jwt_auth)
    def protected_endpoint(request):
        user = request.auth
        return {"user": user.name, "roles": user.roles}
"""

# Authentication backends
from .auth import (
    AuthenticatedUser,
    JWTAuth,
    RoleBasedJWTAuth,
    OptionalJWTAuth,
    jwt_auth,
    optional_jwt_auth,
    proteomics_auth,
    essentiality_auth,
    fitness_auth,
    experimental_data_auth,
    get_authenticated_user,
    require_role,
    require_any_role,
)

# Roles and permissions
from .roles import (
    APIRoles,
    RolePresets,
    get_role_choices,
    validate_roles,
)

# JWT utilities
from .utils import (
    generate_jwt_token,
    decode_jwt_token,
    validate_token_format,
    extract_token_from_header,
    get_token_info,
    get_jwt_secret_key,
    get_jwt_algorithm,
    get_jwt_expiry_days,
)

__all__ = [
    # Authentication backends
    "AuthenticatedUser",
    "JWTAuth",
    "RoleBasedJWTAuth",
    "OptionalJWTAuth",
    # Pre-configured instances
    "jwt_auth",
    "optional_jwt_auth",
    "proteomics_auth",
    "essentiality_auth",
    "fitness_auth",
    "experimental_data_auth",
    # Helper functions
    "get_authenticated_user",
    "require_role",
    "require_any_role",
    # Roles
    "APIRoles",
    "RolePresets",
    "get_role_choices",
    "validate_roles",
    # JWT utilities
    "generate_jwt_token",
    "decode_jwt_token",
    "validate_token_format",
    "extract_token_from_header",
    "get_token_info",
    "get_jwt_secret_key",
    "get_jwt_algorithm",
    "get_jwt_expiry_days",
]

