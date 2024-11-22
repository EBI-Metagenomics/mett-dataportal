import factory
from dataportal.models import Species


class SpeciesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Species
        skip_postgeneration_save = True

    # id = factory.Sequence(lambda n: n + 1)

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

    @factory.post_generation
    def customize_species(obj, create, extracted, **kwargs):
        if extracted:
            for key, value in extracted.items():
                setattr(obj, key, value)
        if create:
            obj.save()
