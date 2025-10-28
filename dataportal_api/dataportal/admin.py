"""
Django admin configuration for METT Data Portal.

This module configures the admin interface for managing API tokens
and other administrative tasks.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django import forms
from dataportal.models import APIToken, Role
from dataportal.authentication import generate_jwt_token, APIRoles, RolePresets


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Admin interface for managing roles.
    
    Allows creation and management of roles that can be assigned to API tokens.
    """
    
    list_display = [
        "name",
        "code",
        "category",
        "is_active",
        "token_count",
        "sort_order",
    ]
    
    list_filter = [
        "category",
        "is_active",
    ]
    
    search_fields = [
        "name",
        "code",
        "description",
    ]
    
    fieldsets = (
        ("Role Information", {
            "fields": ("code", "name", "description"),
        }),
        ("Categorization", {
            "fields": ("category", "sort_order"),
        }),
        ("Status", {
            "fields": ("is_active",),
        }),
    )
    
    readonly_fields = []
    
    def token_count(self, obj):
        """Display count of active tokens with this role."""
        count = obj.tokens.filter(is_active=True).count()
        if count > 0:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 3px;">{} token{}</span>',
                count,
                's' if count != 1 else ''
            )
        return format_html('<span style="color: #999;">0 tokens</span>')
    token_count.short_description = "Active Tokens"


class APITokenForm(forms.ModelForm):
    """Custom form for API Token to make token field optional during creation."""
    
    token = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'cols': 80,
            'placeholder': 'Leave empty to auto-generate a new JWT token'
        }),
        help_text='Leave this field empty to automatically generate a new JWT token. '
                  'Or paste an existing token here if needed.'
    )
    
    # Add role preset dropdown for easier selection
    role_preset = forms.ChoiceField(
        required=False,
        choices=[
            ('', '-- Select a preset or choose individual roles below --'),
            ('full', 'Full Access (Admin)'),
            ('experimental_data_basic', 'Experimental Data Basic (Common experimental data)'),
            ('experimental_interaction_data', 'All experimental and interactions data'),
            ('experimental_only', 'Experimental Data Only'),
            ('interactions_only', 'Interaction Data Only')
        ],
        help_text='Quick presets for common role combinations. Individual roles will be set based on selection.'
    )
    
    class Meta:
        model = APIToken
        fields = '__all__'
        widgets = {
            'roles': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make roles field use checkboxes for easier selection
        if 'roles' in self.fields:
            # Organize roles by category
            self.fields['roles'].queryset = Role.objects.filter(is_active=True).order_by('category', 'sort_order', 'name')
            self.fields['roles'].help_text = (
                'Select one or more roles to grant access to specific API endpoints. '
                'Admin role grants full access to all endpoints.'
            )


@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    """
    Admin interface for managing API tokens.
    
    Features:
    - Generate new JWT tokens directly from admin (leave token field empty)
    - View token details and usage
    - Activate/deactivate tokens
    - Set expiration dates
    """
    
    form = APITokenForm
    
    list_display = [
        "name",
        "status_badge",
        "roles_display",
        "created_at",
        "expires_at",
        "last_used_at",
        "created_by",
    ]
    
    list_filter = [
        "is_active",
        "created_at",
        "expires_at",
    ]
    
    search_fields = [
        "name",
        "description",
        "created_by",
    ]
    
    readonly_fields = [
        "token_display",
        "created_at",
        "last_used_at",
        "token_info",
    ]
    
    actions = ["activate_tokens", "deactivate_tokens", "generate_new_token"]
    
    def roles_display(self, obj):
        """Display roles as badges."""
        roles = obj.roles.filter(is_active=True)
        if not roles.exists():
            return format_html('<span style="color: #999;">No roles assigned</span>')
        
        badges = []
        for role in roles:
            # Color-code roles by category
            color_map = {
                'core': '#dc3545',  # Red for core/admin
                'experimental': '#007bff',  # Blue for experimental
                'interaction': '#28a745',  # Green for interactions
                'advanced': '#6c757d',  # Gray for advanced
                'custom': '#6c757d',  # Gray for custom
            }
            color = color_map.get(role.category, '#6c757d')
            
            badges.append(
                f'<span style="background-color: {color}; color: white; padding: 2px 8px; '
                f'border-radius: 3px; margin: 2px; display: inline-block; font-size: 11px;" '
                f'title="{role.description}">{role.name}</span>'
            )
        
        return format_html(' '.join(badges))
    roles_display.short_description = "Roles"
    
    def get_fieldsets(self, request, obj=None):
        """
        Customize fieldsets based on whether we're adding or editing.
        When adding, hide token_display and token_info since there's no token yet.
        """
        if obj:  # Editing existing token
            return (
                ("Token Identity", {
                    "fields": ("name", "description", "created_by"),
                }),
                ("Roles & Permissions", {
                    "fields": ("role_preset", "roles"),
                    "description": "Assign roles to control access to different API endpoints. "
                                 "Use presets for quick setup or select individual roles.",
                }),
                ("Token Details", {
                    "fields": ("token_display", "token_info"),
                    "description": "The JWT token is displayed below. Copy it from the textarea.",
                }),
                ("Status & Expiration", {
                    "fields": ("is_active", "expires_at"),
                }),
                ("Usage Information", {
                    "fields": ("created_at", "last_used_at"),
                }),
            )
        else:  # Adding new token
            return (
                ("Token Identity", {
                    "fields": ("name", "description", "created_by"),
                    "description": "Enter a unique name for this token (e.g., 'stakeholder1', 'reviewer_john').",
                }),
                ("Roles & Permissions", {
                    "fields": ("role_preset", "roles"),
                    "description": "Assign roles to control access to different API endpoints. "
                                 "Use the preset dropdown for common combinations or select individual roles below.",
                }),
                ("Token Generation", {
                    "fields": ("token",),
                    "description": "<strong>⚠️ LEAVE TOKEN FIELD EMPTY</strong> to automatically generate a new JWT token. "
                                 "The token will be displayed after you save.",
                }),
                ("Status & Expiration", {
                    "fields": ("is_active", "expires_at"),
                    "description": "Set token status and optional expiration date.",
                }),
            )
    
    def status_badge(self, obj):
        """Display a colored badge for token status."""
        if not obj.is_active:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
                'border-radius: 3px;">Inactive</span>'
            )
        elif obj.is_expired():
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 10px; '
                'border-radius: 3px;">Expired</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px;">Active</span>'
            )
    status_badge.short_description = "Status"
    
    def token_display(self, obj):
        """Display the token in a copyable format."""
        if obj.token:
            # Show first 20 and last 20 characters with ... in between
            if len(obj.token) > 50:
                display_token = f"{obj.token[:20]}...{obj.token[-20:]}"
            else:
                display_token = obj.token
            
            return format_html(
                '<div style="font-family: monospace; background-color: #f5f5f5; '
                'padding: 10px; border-radius: 4px; word-break: break-all;">{}</div>'
                '<p style="margin-top: 10px;"><strong>Full token:</strong></p>'
                '<textarea readonly style="width: 100%; height: 100px; font-family: monospace; '
                'padding: 5px;">{}</textarea>',
                display_token,
                obj.token
            )
        return "-"
    token_display.short_description = "Token (Copy from textarea below)"
    
    def token_info(self, obj):
        """Display decoded token information."""
        if not obj.token:
            return "-"
        
        from dataportal.authentication import get_token_info
        info = get_token_info(obj.token)
        
        if not info:
            return format_html(
                '<span style="color: red;">Invalid token format</span>'
            )
        
        html = '<table style="border-collapse: collapse;">'
        for key, value in info.items():
            # Format timestamps
            if key in ["iat", "exp"] and isinstance(value, (int, float)):
                dt = timezone.datetime.fromtimestamp(value, tz=timezone.utc)
                value = f"{dt.strftime('%Y-%m-%d %H:%M:%S UTC')} ({value})"
            
            html += f'<tr><td style="padding: 5px; font-weight: bold;">{key}:</td>' \
                   f'<td style="padding: 5px; font-family: monospace;">{value}</td></tr>'
        html += '</table>'
        
        return format_html(html)
    token_info.short_description = "Decoded Token Info (unverified)"
    
    def save_model(self, request, obj, form, change):
        """
        Override save to auto-generate token if not provided and handle role presets.
        Note: M2M fields are saved later in save_related()
        """
        # Set created_by if not set
        if not obj.created_by and request.user.is_authenticated:
            obj.created_by = request.user.username
        
        # Save the basic model first
        super().save_model(request, obj, form, change)
        
        # Store flag for later use in save_related
        self._token_was_generated = False
    
    def save_related(self, request, form, formsets, change):
        """
        Override to handle M2M relationships and regenerate token with roles.
        This is called AFTER save_model, when M2M data is available.
        """
        # Save M2M relationships first (this saves the roles)
        super().save_related(request, form, formsets, change)
        
        obj = form.instance
        
        # Handle role preset selection (after super().save_related())
        role_preset = form.cleaned_data.get('role_preset')
        if role_preset:
            preset_map = {
                'full': RolePresets.full_access,
                'experimental_data_basic': RolePresets.experimental_data_basic,
                'experimental_interaction_data': RolePresets.experimental_interaction_data,
                'experimental_only': RolePresets.experimental_only,
                'interactions_only': RolePresets.interactions_only
            }
            if role_preset in preset_map:
                role_codes = preset_map[role_preset]()
                # Get Role objects by code
                roles_to_assign = Role.objects.filter(code__in=role_codes, is_active=True)
                obj.roles.set(roles_to_assign)
        
        # Get current role codes (after M2M save)
        role_codes = obj.get_role_codes()
        
        # Check if we need to generate or regenerate token
        should_regenerate = False
        
        # If no token exists, generate one
        if not obj.token or obj.token == "temporary":
            should_regenerate = True
            self._token_was_generated = True
        
        # If roles changed, regenerate token
        elif change:
            # This is an edit - check if roles changed
            # We can't easily compare here, so regenerate if roles exist
            # Alternative: always regenerate on save with roles
            if role_codes:
                should_regenerate = True
        
        # Generate/regenerate token with roles
        if should_regenerate:
            obj.token = generate_jwt_token(
                name=obj.name,
                roles=role_codes,
                expiry_days=None,
                token_id=obj.pk,
                created_by=obj.created_by
            )
            obj.save(update_fields=['token'])
            
            if self._token_was_generated:
                # New token created
                roles_str = ', '.join(role_codes) if role_codes else 'No roles'
                self.message_user(
                    request,
                    f"✅ JWT token for '{obj.name}' has been generated successfully! "
                    f"Roles: {roles_str}. "
                    f"Scroll down to see the full token and copy it from the textarea.",
                    level='success'
                )
            else:
                # Token regenerated due to role change
                self.message_user(
                    request,
                    f"⚠️ Token has been regenerated with updated roles. "
                    f"Old token is now invalid!",
                    level='warning'
                )
    
    def activate_tokens(self, request, queryset):
        """Admin action to activate selected tokens."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"{updated} token(s) activated successfully."
        )
    activate_tokens.short_description = "Activate selected tokens"
    
    def deactivate_tokens(self, request, queryset):
        """Admin action to deactivate selected tokens."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} token(s) deactivated successfully."
        )
    deactivate_tokens.short_description = "Deactivate selected tokens"
    
    def generate_new_token(self, request, queryset):
        """Admin action to regenerate tokens for selected entries."""
        count = 0
        for token_obj in queryset:
            # Generate new token
            token_obj.token = generate_jwt_token(
                name=token_obj.name,
                expiry_days=None
            )
            token_obj.save()
            count += 1
        
        self.message_user(
            request,
            f"{count} token(s) regenerated successfully. "
            "Note: Old tokens are now invalid!"
        )
    generate_new_token.short_description = "Regenerate tokens (WARNING: Invalidates old tokens)"
    
    class Media:
        css = {
            'all': ('admin/css/forms.css',)
        }
