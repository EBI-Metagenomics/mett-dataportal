"""
JWT Authentication utilities for API token management.

This module provides functions to generate and validate JWT tokens
using PyJWT library.
"""

import jwt
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.conf import settings


def get_jwt_secret_key() -> str:
    """
    Get the JWT secret key from settings.
    Falls back to Django SECRET_KEY if JWT_SECRET_KEY is not set.
    """
    return getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)


def get_jwt_algorithm() -> str:
    """Get the JWT algorithm from settings."""
    return getattr(settings, "JWT_ALGORITHM", "HS256")


def get_jwt_expiry_days() -> Optional[int]:
    """
    Get JWT token expiry in days from settings.
    Returns None for non-expiring tokens.
    """
    return getattr(settings, "JWT_EXPIRY_DAYS", None)


def generate_jwt_token(
    name: str,
    expiry_days: Optional[int] = None,
    roles: Optional[list] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
    token_id: Optional[int] = None,
    created_by: Optional[str] = None
) -> str:
    """
    Generate a JWT token for a given user identifier with enhanced metadata.
    
    Args:
        name: Unique identifier/name for the token holder
        expiry_days: Number of days until token expires (None = never expires)
        roles: List of roles/permissions for this token
        additional_claims: Optional additional claims to include in the token
        token_id: Database ID of the APIToken (for tracking)
        created_by: Who created this token
        
    Returns:
        JWT token string
        
    Example:
        >>> token = generate_jwt_token(
        ...     "stakeholder1", 
        ...     roles=["proteomics", "essentiality"],
        ...     created_by="admin"
        ... )
    """
    if expiry_days is None:
        expiry_days = get_jwt_expiry_days()
    
    # Use Unix timestamp (int) instead of datetime to avoid timezone issues
    now = int(time.time())
    
    # Base payload with standard JWT claims
    payload = {
        # Standard JWT claims (https://www.rfc-editor.org/rfc/rfc7519#section-4.1)
        "sub": name,  # Subject - who this token is for
        "iat": now,  # Issued at (Unix timestamp)
        "jti": secrets.token_urlsafe(16),  # JWT ID - unique identifier for this token
        "iss": "mett-dataportal",  # Issuer - identifies the system that issued the token
        "aud": "mett-dataportal-api",  # Audience - identifies the intended recipient
        
        # Custom claims for enhanced functionality
        "token_type": "api_access",  # Type of token
        "token_version": "1.0",  # Token schema version (for future compatibility)
    }
    
    # Add roles with metadata
    if roles:
        payload["roles"] = roles  # List of role codes
        payload["role_count"] = len(roles)  # Quick count for logging
        
        # Add role categories for quick filtering
        role_categories = set()
        if "admin" in roles:
            role_categories.add("admin")
        for role in roles:
            if role in ["proteomics", "essentiality", "fitness", "mutant_growth", "reactions", "drugs"]:
                role_categories.add("experimental")
            elif role in ["ppi", "ttp", "fitness_correlation", "orthologs", "operons"]:
                role_categories.add("interaction")
            elif role in ["natural_query", "pyhmmer_search"]:
                role_categories.add("advanced")
        
        if role_categories:
            payload["role_categories"] = list(role_categories)
    
    # Add token database ID for tracking
    if token_id:
        payload["token_id"] = token_id
    
    # Add creator information
    if created_by:
        payload["created_by"] = created_by
    
    # Add expiration if specified
    if expiry_days is not None:
        payload["exp"] = now + (expiry_days * 24 * 60 * 60)  # Convert days to seconds
        payload["nbf"] = now  # Not before - token valid from now
    
    # Add any additional custom claims
    if additional_claims:
        payload.update(additional_claims)
    
    # Generate token
    token = jwt.encode(
        payload,
        get_jwt_secret_key(),
        algorithm=get_jwt_algorithm()
    )
    
    return token


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dict if valid, None if invalid
        
    Example:
        >>> payload = decode_jwt_token(token)
        >>> if payload:
        ...     user_name = payload.get("sub")
    """
    try:
        # Decode token with audience and issuer validation
        payload = jwt.decode(
            token,
            get_jwt_secret_key(),
            algorithms=[get_jwt_algorithm()],
            audience="mett-dataportal-api",  # Must match token's aud claim
            issuer="mett-dataportal",  # Must match token's iss claim
            options={
                "verify_signature": True,
                "verify_exp": True,  # Verify expiration if present
                "verify_aud": True,  # Verify audience
                "verify_iss": True,  # Verify issuer
            }
        )
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.InvalidAudienceError:
        # Wrong audience
        return None
    except jwt.InvalidIssuerError:
        # Wrong issuer
        return None
    except jwt.InvalidTokenError:
        # Token is invalid (malformed, wrong signature, etc.)
        return None
    except Exception:
        # Any other error
        return None


def validate_token_format(token: str) -> bool:
    """
    Validate that a string looks like a JWT token.
    
    Args:
        token: String to validate
        
    Returns:
        True if the string has JWT format (3 parts separated by dots)
    """
    if not token:
        return False
    
    parts = token.split(".")
    return len(parts) == 3


def extract_token_from_header(authorization_header: str) -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Expected format: "Bearer <token>"
    
    Args:
        authorization_header: The Authorization header value
        
    Returns:
        Token string if found, None otherwise
        
    Example:
        >>> token = extract_token_from_header("Bearer eyJhbG...")
    """
    if not authorization_header:
        return None
    
    parts = authorization_header.split()
    
    if len(parts) != 2:
        return None
    
    scheme, token = parts
    
    if scheme.lower() != "bearer":
        return None
    
    return token


def get_token_info(token: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a token without validating signature.
    Useful for debugging or displaying token info in admin.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dict (unverified) or None
        
    Warning:
        This does NOT validate the token signature!
        Only use for display purposes, not authentication.
    """
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        return payload
    except Exception:
        return None

