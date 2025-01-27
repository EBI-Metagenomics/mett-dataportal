import factory
from dataportal.models import Species


class SpeciesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Species

    id = factory.Sequence(lambda n: n + 1)

    scientific_name = factory.Iterator(
        [
            "Bacteroides uniformis",
            "Phocaeicola vulgatus",
        ]
    )
    common_name = factory.Iterator(
        [
            "Bacteroides",
            "Bacteroides vulgatus",
        ]
    )
    acronym = factory.Iterator(
        [
            "BU",
            "PV",
        ]
    )

    taxonomy_id = factory.Sequence(lambda n: n + 100)
