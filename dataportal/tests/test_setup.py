import logging
import os
import time

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings

from dataportal.models import SpeciesData
from dataportal.utils.fts_utils import FullTextSearchManager

logger = logging.getLogger(__name__)

@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(settings.BASE_DIR, 'test_db.sqlite3'),  # Use a file-based SQLite database for testing
    }
})
class BaseTestSetup(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ensure the test database is clean
        test_db = settings.DATABASES['default']['NAME']
        if os.path.exists(test_db):
            os.remove(test_db)

        # Apply migrations
        logger.info("Applying migrations")
        call_command('migrate')

    def setUp(self):
        super().setUp()

        # Print the database settings to verify the test configuration
        logger.info(f"Using database settings: {settings.DATABASES}")

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
        logger.info("FTS table created and populated.")

        # Notify that the setup is complete and wait
        print("Test database setup complete. You can now check the database file manually.")
        time.sleep(60)  # Pause for 60 seconds

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up the test database file
        test_db = settings.DATABASES['default']['NAME']
        if os.path.exists(test_db):
            os.remove(test_db)
