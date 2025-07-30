import factory

from dataportal.models import GeneDocument


class GeneFactory(factory.Factory):
    class Meta:
        model = GeneDocument

    gene_id = factory.Sequence(lambda n: n + 1)
    gene_name = factory.Iterator(["geneA", "geneB", "geneC", "geneD"])
    locus_tag = factory.Sequence(lambda n: f"LOCUS{n}")
    product = factory.Iterator(["Product A", "Product B", "Product C", "Product D"])
    start = factory.Sequence(lambda n: 100 + n * 100)
    end = factory.Sequence(lambda n: 200 + n * 100)
    isolate_name = factory.Iterator(["BU_ATCC8492"])
    species_acronym = factory.Iterator(["BU"])
    species_scientific_name = factory.Iterator(["Bacteroides uniformis"])

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(**kwargs)
        obj.save()
        return obj
