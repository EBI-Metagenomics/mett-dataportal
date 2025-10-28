"""
Management command to generate API tokens from command line.

This provides a convenient way to create tokens without using Django Admin.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta

from dataportal.models import APIToken, Role
from dataportal.authentication import generate_jwt_token, RolePresets


class Command(BaseCommand):
    help = 'Generate a new API token for authentication'

    def add_arguments(self, parser):
        parser.add_argument(
            'name',
            type=str,
            help='Unique name/identifier for the token (e.g., stakeholder1)'
        )
        parser.add_argument(
            '--description',
            type=str,
            default='',
            help='Optional description of the token purpose'
        )
        parser.add_argument(
            '--created-by',
            type=str,
            default='',
            help='Name of person creating the token'
        )
        parser.add_argument(
            '--expires-in-days',
            type=int,
            default=None,
            help='Number of days until token expires (default: never)'
        )
        parser.add_argument(
            '--inactive',
            action='store_true',
            help='Create the token in inactive state'
        )
        parser.add_argument(
            '--roles',
            type=str,
            default='',
            help='Comma-separated list of roles (e.g., "proteomics,essentiality,fitness")'
        )
        parser.add_argument(
            '--role-preset',
            type=str,
            choices=['full', 'experimental_data_basic', 'experimental_interaction_data', 'experimental_only', 'interactions_only'],
            help='Use a role preset instead of specifying individual roles'
        )

    def handle(self, *args, **options):
        name = options['name']
        description = options['description']
        created_by = options['created_by']
        expires_in_days = options['expires_in_days']
        is_active = not options['inactive']
        roles_str = options['roles']
        role_preset = options['role_preset']

        # Check if token with this name already exists
        if APIToken.objects.filter(name=name).exists():
            raise CommandError(f'Token with name "{name}" already exists.')

        # Determine role codes
        role_codes = []
        if role_preset:
            preset_map = {
                'full': RolePresets.full_access,
                'experimental_data_basic': RolePresets.experimental_data_basic,
                'experimental_interaction_data': RolePresets.experimental_interaction_data,
                'experimental_only': RolePresets.experimental_only,
                'interactions_only': RolePresets.interactions_only,
            }
            role_codes = preset_map[role_preset]()
            self.stdout.write(f'Using role preset: {role_preset}')
        elif roles_str:
            role_codes = [r.strip() for r in roles_str.split(',') if r.strip()]

        # Get Role objects from database
        role_objects = Role.objects.filter(code__in=role_codes, is_active=True)
        if role_codes and not role_objects.exists():
            raise CommandError(
                f'No active roles found for codes: {role_codes}. '
                f'Please run "python manage.py seed_roles" first.'
            )

        # Calculate expiration date
        expires_at = None
        if expires_in_days is not None:
            expires_at = timezone.now() + timedelta(days=expires_in_days)

        # Create token in database first (to get ID)
        api_token = APIToken.objects.create(
            name=name,
            token="temporary",  # Temporary placeholder
            description=description,
            created_by=created_by,
            is_active=is_active,
            expires_at=expires_at,
        )
        
        # Assign roles (many-to-many)
        if role_objects.exists():
            api_token.roles.set(role_objects)
        
        # Generate JWT token with full metadata including database ID
        token = generate_jwt_token(
            name=name,
            roles=role_codes,
            expiry_days=expires_in_days,
            token_id=api_token.pk,  # Include database ID
            created_by=created_by  # Include creator
        )
        
        # Update with real token
        api_token.token = token
        api_token.save(update_fields=['token'])

        # Output results
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*70}\n'
            f'API Token created successfully!\n'
            f'{"="*70}\n'
        ))
        self.stdout.write(f'Name:        {api_token.name}')
        self.stdout.write(f'Status:      {"Active" if api_token.is_active else "Inactive"}')
        self.stdout.write(f'Created:     {api_token.created_at}')
        
        if api_token.expires_at:
            self.stdout.write(f'Expires:     {api_token.expires_at}')
        else:
            self.stdout.write(f'Expires:     Never')
        
        if description:
            self.stdout.write(f'Description: {description}')
        
        assigned_roles = api_token.get_role_codes()
        if assigned_roles:
            self.stdout.write(f'Roles:       {", ".join(assigned_roles)}')
        else:
            self.stdout.write(f'Roles:       None (no role-based restrictions)')
        
        self.stdout.write(f'\n{"-"*70}')
        self.stdout.write('Token (copy this):')
        self.stdout.write(f'{"-"*70}\n')
        self.stdout.write(self.style.WARNING(token))
        self.stdout.write(f'\n{"-"*70}')
        self.stdout.write('\nUsage:')
        self.stdout.write('  curl -H "Authorization: Bearer <TOKEN>" http://your-api-url/endpoint')
        self.stdout.write(f'\n{"="*70}\n')

