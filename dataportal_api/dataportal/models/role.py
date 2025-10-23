"""
Role model for role-based access control.

This model stores role definitions that can be assigned to API tokens.
"""

from django.db import models


class Role(models.Model):
    """
    Defines a role that can be assigned to API tokens.
    
    Roles control access to different API endpoints and features.
    """
    
    # Role identification
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique code for this role (e.g., 'proteomics', 'admin')"
    )
    
    name = models.CharField(
        max_length=100,
        help_text="Human-readable name for this role"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Detailed description of what this role grants access to"
    )
    
    # Categorization
    CATEGORY_CHOICES = [
        ('core', 'Core Access'),
        ('experimental', 'Experimental Data'),
        ('interaction', 'Interaction Data'),
        ('advanced', 'Advanced Features'),
        ('custom', 'Custom Role'),
    ]
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='custom',
        help_text="Category for organizing roles"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this role is active and can be assigned to tokens"
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this role was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this role was last updated"
    )
    
    # Ordering
    sort_order = models.IntegerField(
        default=0,
        help_text="Order for displaying roles (lower numbers first)"
    )
    
    class Meta:
        db_table = "roles"
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ['category', 'sort_order', 'name']
        indexes = [
            models.Index(fields=['code'], name='idx_role_code'),
            models.Index(fields=['is_active'], name='idx_role_active'),
            models.Index(fields=['category'], name='idx_role_category'),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def save(self, *args, **kwargs):
        """Ensure code is lowercase."""
        self.code = self.code.lower().replace(' ', '_')
        super().save(*args, **kwargs)

