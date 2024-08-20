import os
import pytest
from django.conf import settings
from django.core.management import call_command
from django.db import connection


@pytest.fixture(scope='session')
def django_db_setup(django_db_blocker):
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # Use in-memory database for tests
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
        'CONN_MAX_AGE': 0,
        'OPTIONS': {},
        'TIME_ZONE': None,
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
    with django_db_blocker.unblock():
        call_command('migrate')
        call_command('collectstatic', interactive=False, clear=True)



@pytest.fixture(scope='function')
def fts_setup(django_db_setup, db):
    from dataportal.models import Species, Strain, Gene

    # Create test data in the database
    species1 = Species.objects.create(
        scientific_name="Bacteroides uniformis",
        common_name="Uniformis",
        taxonomy_id=1
    )
    species2 = Species.objects.create(
        scientific_name="Phocaeicola vulgatus",
        common_name="Vulgatus",
        taxonomy_id=2
    )

    strain1 = Strain.objects.create(
        species=species1,
        isolate_name="BU_2243B",
        strain_name="Strain BU_2243B",
        assembly_name="BU_2243B_NT5389.1",
        assembly_accession="NT5389.1",
        fasta_file="BU_2243B_NT5389.1.fa",
        gff_file="BU_2243B_annotations.gff"
    )
    strain2 = Strain.objects.create(
        species=species2,
        isolate_name="PV_H4-2",
        strain_name="Strain PV_H4-2",
        assembly_name="PV_H42_NT5107.1",
        assembly_accession="NT5107.1",
        fasta_file="PV_H42_NT5107.1.fa",
        gff_file="PV_H4-2_annotations.gff"
    )

    # Add more strains as needed
    # ...

    # Manually create and populate the FTS tables
    with connection.cursor() as cursor:
        # Clear existing data in FTS tables if they exist
        cursor.execute('DELETE FROM species_fts;')
        cursor.execute('DELETE FROM strain_fts;')
        cursor.execute('DELETE FROM gene_fts;')

        # Populate Species FTS table
        cursor.execute('''
            INSERT INTO species_fts(rowid, scientific_name, common_name)
            SELECT id, scientific_name, common_name FROM species;
        ''')

        # Populate Strain FTS table
        cursor.execute('''
            INSERT INTO strain_fts(rowid, isolate_name, strain_name, assembly_name, fasta_file, gff_file)
            SELECT id, isolate_name, strain_name, assembly_name, fasta_file, gff_file FROM strain;
        ''')

        # Populate Gene FTS table if needed
        cursor.execute('''
            INSERT INTO gene_fts(rowid, gene_id, gene_name, gene_symbol, locus_tag)
            SELECT id, gene_id, gene_name, gene_symbol, locus_tag FROM gene;
        ''')

    print("FTS tables created and populated.")

    yield

    # Optional: Add any necessary cleanup code here
