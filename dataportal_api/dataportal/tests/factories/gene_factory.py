import factory

from dataportal.models import Gene, EssentialityTag
from dataportal.tests.factories.strain_factory import StrainFactory


class GeneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Gene

    id = factory.Sequence(lambda n: n + 1)
    gene_name = factory.Iterator(["geneA", "geneB", "geneC", "geneD"])
    locus_tag = factory.Sequence(lambda n: f"LOCUS{n}")
    description = factory.Iterator(
        ["Gene A description", "Gene B description", "Gene C description", "Gene D description"])
    product = factory.Iterator(["Product A", "Product B", "Product C", "Product D"])
    start_position = factory.Sequence(lambda n: 100 + n * 100)
    end_position = factory.Sequence(lambda n: 200 + n * 100)
    strain = factory.SubFactory(StrainFactory)


class EssentialityTagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EssentialityTag

    name = factory.Sequence(lambda n: f"EssentialityTag{n}")
