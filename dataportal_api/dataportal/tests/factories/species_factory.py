import factory

from dataportal.models import SpeciesDocument


class SpeciesFactory(factory.Factory):
    class Meta:
        model = SpeciesDocument

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

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(**kwargs)
        obj.save()
        return obj
