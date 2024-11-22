import factory

from dataportal.models import Strain
from dataportal.tests.factories.species_factory import SpeciesFactory


class StrainFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Strain

    id = factory.Sequence(lambda n: n + 1)
    isolate_name = factory.Iterator(["Strain A", "Strain B"])
    assembly_name = factory.Iterator(["Assembly A", "Assembly B"])
    assembly_accession = factory.Sequence(lambda n: n + 100)
    fasta_file = factory.Iterator(["fileA.fasta", "fileB.fasta"])
    gff_file = factory.Iterator(["fileA.gff", "fileB.gff"])
    type_strain = factory.Iterator([True, False])
    species = factory.SubFactory(SpeciesFactory)
