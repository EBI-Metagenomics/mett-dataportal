from django.test import TestCase
from dataportal.models import SpeciesData

class BaseTestSetup(TestCase):

    def setUp(self):
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
