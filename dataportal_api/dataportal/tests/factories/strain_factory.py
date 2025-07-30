import factory

from dataportal.models import StrainDocument
from dataportal.tests.factories.species_factory import SpeciesFactory


class StrainFactory(factory.Factory):
    class Meta:
        model = StrainDocument

    isolate_name = factory.Iterator(
        ["BU_ATCC8492", "BU_2243B", "BU_3537", "PV_ATCC8482"]
    )
    assembly_name = factory.Iterator(
        [
            "BU_ATCC8492VPI0062_NT5002.1",
            "BU_2243B_NT5389.1",
            "BU_3537_NT5405.1",
            "PV_ATCC8482DSM1447_NT5001.1",
        ]
    )
    assembly_accession = factory.Sequence(lambda n: f"ASM{1000 + n}")
    fasta_file = factory.Iterator(
        [
            "BU_ATCC8492VPI0062_NT5002.1.fa",
            "BU_2243B_NT5389.1.fa",
            "BU_3537_NT5405.1.fa",
            "PV_ATCC8482DSM1447_NT5001.1.fa",
        ]
    )
    gff_file = factory.Iterator(
        [
            "BU_ATCC8492_annotations.gff",
            "BU_2243B_annotations.gff",
            "BU_3537_annotations.gff",
            "PV_ATCC8482_annotations.gff",
        ]
    )
    type_strain = factory.Iterator([True, False, False, True])
    species_scientific_name = factory.LazyAttribute(
        lambda _: SpeciesFactory().scientific_name
    )
    species_acronym = factory.LazyAttribute(lambda _: SpeciesFactory().acronym)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(**kwargs)
        obj.save()
        return obj
