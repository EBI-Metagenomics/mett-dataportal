import os
import pytest
from django.conf import settings
from django.core.management import call_command

@pytest.fixture(scope='session')
def django_db_setup(django_db_blocker):
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(settings.BASE_DIR, 'test_db.sqlite3'),
        'ATOMIC_REQUESTS': False,  # Add the missing key
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
    from dataportal.models import SpeciesData
    from dataportal.utils.fts_utils import FullTextSearchManager

    # Create test data
    SpeciesData.objects.create(
        species="Bacteroides uniformis", isolate_name="BU_2243B",
        assembly_name="BU_2243B_NT5389.1", fasta_file="BU_2243B_NT5389.1.fa",
        gff_file="BU_2243B_annotations.gff"
    )
    SpeciesData.objects.create(
        species="Bacteroides uniformis", isolate_name="BU_3537",
        assembly_name="BU_3537_NT5405.1", fasta_file="BU_3537_NT5405.1.fa",
        gff_file="BU_3537_annotations.gff"
    )
    SpeciesData.objects.create(
        species="Bacteroides uniformis", isolate_name="BU_61",
        assembly_name="BU_61_NT5381.1", fasta_file="BU_61_NT5381.1.fa",
        gff_file="BU_61_annotations.gff"
    )
    SpeciesData.objects.create(
        species="Phocaeicola vulgatus", isolate_name="PV_H4-2",
        assembly_name="PV_H42_NT5107.1", fasta_file="PV_H42_NT5107.1.fa",
        gff_file="PV_H4-2_annotations.gff"
    )
    SpeciesData.objects.create(
        species="Phocaeicola vulgatus", isolate_name="PV_H5-1",
        assembly_name="PV_H51_NT5108.1", fasta_file="PV_H51_NT5108.1.fa",
        gff_file="PV_H5-1_annotations.gff"
    )
    SpeciesData.objects.create(
        species="Phocaeicola vulgatus", isolate_name="PV_H6-5",
        assembly_name="PV_H65_NT5109.1", fasta_file="PV_H65_NT5109.1.fa",
        gff_file="PV_H6-5_annotations.gff"
    )

    # Manually create and populate the FTS table
    fts_manager = FullTextSearchManager(
        table_name='speciesdata',
        fields=['species', 'isolate_name', 'assembly_name', 'fasta_file', 'gff_file']
    )
    fts_manager.create_full_text_search_table()
    fts_manager.update_full_text_search()
    print("FTS table created and populated.")

    yield

    # Cleanup if necessary
