"""
Django model for API Token management.

This model stores JWT tokens for API authentication, allowing long-lived
tokens that can be managed through Django admin.
"""

from django.db import models
from django.utils import timezone


class APIToken(models.Model):
    """
    Model to store API tokens for authentication.
    
    Tokens are associated with a user name/identifier and can be
    managed through Django admin interface.
    """
    
    # User identification
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique name/identifier for this token (e.g., 'stakeholder1', 'reviewer_john')"
    )
    
    # Token details
    token = models.TextField(
        unique=True,
        help_text="The actual JWT token string"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description of what this token is used for"
    )
    
    # Status and lifecycle
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this token is currently active and can be used for authentication"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this token was created"
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this token expires (null = never expires)"
    )
    
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this token was last used for authentication"
    )
    
    # Metadata
    created_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Who created this token"
    )
    
    # Role-based access control (many-to-many relationship)
    roles = models.ManyToManyField(
        'Role',
        blank=True,
        related_name='tokens',
        help_text="Roles assigned to this token"
    )
    
    class Meta:
        db_table = "api_tokens"
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token"], name="idx_api_token"),
            models.Index(fields=["is_active"], name="idx_api_token_active"),
        ]
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} ({status})"
    
    def is_expired(self):
        """Check if the token has expired."""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if the token is valid (active and not expired)."""
        return self.is_active and not self.is_expired()
    
    def mark_as_used(self):
        """Update the last_used_at timestamp."""
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])
    
    def get_role_codes(self) -> list:
        """
        Get list of role codes assigned to this token.
        
        Returns:
            List of role code strings
        """
        return list(self.roles.filter(is_active=True).values_list('code', flat=True))
    
    def has_role(self, role_code: str) -> bool:
        """
        Check if this token has a specific role.
        
        Args:
            role_code: Role code to check (e.g., 'proteomics', 'admin')
            
        Returns:
            True if token has the role, False otherwise
        """
        return self.roles.filter(code=role_code, is_active=True).exists()
    
    def has_any_role(self, role_codes: list) -> bool:
        """
        Check if this token has any of the specified roles.
        
        Args:
            role_codes: List of role codes to check
            
        Returns:
            True if token has at least one of the roles, False otherwise
        """
        return self.roles.filter(code__in=role_codes, is_active=True).exists()
    
    def has_all_roles(self, role_codes: list) -> bool:
        """
        Check if this token has all of the specified roles.
        
        Args:
            role_codes: List of role codes to check
            
        Returns:
            True if token has all the roles, False otherwise
        """
        return self.roles.filter(code__in=role_codes, is_active=True).count() == len(role_codes)

