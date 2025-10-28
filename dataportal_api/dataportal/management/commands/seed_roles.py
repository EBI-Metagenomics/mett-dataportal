"""
Management command to seed predefined roles into the database.

This populates the Role table with all the standard roles defined in APIRoles.
"""

from django.core.management.base import BaseCommand
from dataportal.models import Role
from dataportal.authentication.roles import APIRoles


class Command(BaseCommand):
    help = 'Seed predefined roles into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing roles with new descriptions/categories'
        )

    def handle(self, *args, **options):
        update_existing = options['update']
        
        # Define all roles with their metadata
        roles_data = [
            # Core roles
            {
                'code': APIRoles.ADMIN,
                'name': 'Administrator',
                'description': 'Full access to all API endpoints and administrative functions',
                'category': 'core',
                'sort_order': 1,
            },
            {
                'code': APIRoles.READ_ONLY,
                'name': 'Read Only',
                'description': 'Basic genome and gene browsing access (no experimental data)',
                'category': 'core',
                'sort_order': 2,
            },
            
            # Experimental data roles
            {
                'code': APIRoles.PROTEOMICS,
                'name': 'Proteomics',
                'description': 'Access to proteomics experimental data and analysis',
                'category': 'experimental',
                'sort_order': 10,
            },
            {
                'code': APIRoles.ESSENTIALITY,
                'name': 'Essentiality',
                'description': 'Access to gene essentiality data and predictions',
                'category': 'experimental',
                'sort_order': 11,
            },
            {
                'code': APIRoles.FITNESS,
                'name': 'Fitness',
                'description': 'Access to fitness data and analysis',
                'category': 'experimental',
                'sort_order': 12,
            },
            {
                'code': APIRoles.MUTANT_GROWTH,
                'name': 'Mutant Growth',
                'description': 'Access to mutant growth data and phenotype information',
                'category': 'experimental',
                'sort_order': 13,
            },
            {
                'code': APIRoles.REACTIONS,
                'name': 'Metabolic Reactions',
                'description': 'Access to metabolic reactions and pathway data',
                'category': 'experimental',
                'sort_order': 14,
            },
            {
                'code': APIRoles.DRUGS,
                'name': 'Drug Interactions',
                'description': 'Access to drug interaction data and predictions',
                'category': 'experimental',
                'sort_order': 15,
            },
            
            # Interaction data roles
            {
                'code': APIRoles.PPI,
                'name': 'Protein-Protein Interactions',
                'description': 'Access to protein-protein interaction networks',
                'category': 'interaction',
                'sort_order': 20,
            },
            {
                'code': APIRoles.TTP,
                'name': 'Transcription Factor Targets',
                'description': 'Access to transcription factor-target protein data',
                'category': 'interaction',
                'sort_order': 21,
            },
            {
                'code': APIRoles.FITNESS_CORRELATION,
                'name': 'Fitness Correlation',
                'description': 'Access to fitness correlation data and analysis',
                'category': 'interaction',
                'sort_order': 22,
            },
            {
                'code': APIRoles.ORTHOLOGS,
                'name': 'Orthologs',
                'description': 'Access to ortholog data and cross-species comparisons',
                'category': 'interaction',
                'sort_order': 23,
            },
            {
                'code': APIRoles.OPERONS,
                'name': 'Operons',
                'description': 'Access to operon data and gene organization',
                'category': 'interaction',
                'sort_order': 24,
            },
            
            # Advanced features
            {
                'code': APIRoles.NATURAL_QUERY,
                'name': 'Natural Language Query',
                'description': 'Access to natural language query API for advanced searches',
                'category': 'advanced',
                'sort_order': 30,
            },
            {
                'code': APIRoles.PYHMMER_SEARCH,
                'name': 'PyHMMER Search',
                'description': 'Access to PyHMMER protein similarity search',
                'category': 'advanced',
                'sort_order': 31,
            },
        ]
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for role_data in roles_data:
            code = role_data['code']
            
            # Check if role already exists
            existing_role = Role.objects.filter(code=code).first()
            
            if existing_role:
                if update_existing:
                    # Update existing role
                    for key, value in role_data.items():
                        setattr(existing_role, key, value)
                    existing_role.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated: {role_data["name"]} ({code})')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Exists:  {role_data["name"]} ({code})')
                    )
            else:
                # Create new role
                Role.objects.create(**role_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {role_data["name"]} ({code})')
                )
        
        # Summary
        self.stdout.write(f'\n{"-"*70}')
        self.stdout.write(self.style.SUCCESS(
            f'\nRole seeding complete!\n'
            f'  Created: {created_count}\n'
            f'  Updated: {updated_count}\n'
            f'  Skipped: {skipped_count}\n'
            f'  Total:   {len(roles_data)}\n'
        ))
        
        if skipped_count > 0 and not update_existing:
            self.stdout.write(
                self.style.WARNING(
                    '\nTip: Use --update flag to update existing roles with new descriptions/categories'
                )
            )

