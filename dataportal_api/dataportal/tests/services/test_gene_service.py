import factory
import pytest
from asgiref.sync import sync_to_async

from dataportal.models import GeneEssentiality
from dataportal.services.gene_service import GeneService
from dataportal.tests.factories.gene_factory import GeneFactory, EssentialityTagFactory
from dataportal.tests.factories.strain_factory import StrainFactory
from dataportal.utils.constants import GENE_FIELD_NAME
from dataportal.utils.exceptions import GeneNotFoundError


@pytest.mark.django_db(transaction=True)
class TestGeneService:
    @pytest.mark.asyncio
    async def test_get_gene_by_id(self):
        # Create a gene
        gene = await sync_to_async(GeneFactory.create)()

        service = GeneService()
        result = await service.get_gene_by_id(gene.id)

        assert result.id == gene.id
        assert result.gene_name == gene.gene_name

    @pytest.mark.asyncio
    async def test_get_gene_by_invalid_id(self):
        service = GeneService()
        with pytest.raises(GeneNotFoundError):
            await service.get_gene_by_id(999)  # Non-existent ID

    @pytest.mark.asyncio
    async def test_get_all_genes(self):
        # Create multiple genes
        await sync_to_async(GeneFactory.create_batch)(5)

        service = GeneService()
        result = await service.get_all_genes()

        assert len(result.results) == 5
        assert all(isinstance(gene.id, int) for gene in result.results)

    @pytest.mark.asyncio
    async def test_search_genes(self):
        # Create genes with specific names
        await sync_to_async(GeneFactory.create_batch)(
            3, gene_name=factory.Iterator(["testGene1", "testGene2", "otherGene"])
        )

        service = GeneService()
        result = await service.search_genes(query="testGene")

        assert len(result.results) == 2
        assert all("testGene" in gene.gene_name for gene in result.results)

    @pytest.mark.asyncio
    async def test_get_genes_by_genome(self):
        strain = await sync_to_async(StrainFactory.create)()
        print(f"Strain created: {strain} (type: {type(strain)})")

        await sync_to_async(GeneFactory.create_batch)(3, strain=strain)
        print("Genes created successfully.")

        service = GeneService()
        result = await service.get_genes_by_genome(genome_id=strain.id)
        print(f"Service result: {result}")

        assert len(result.results) == 3
        for gene in result.results:
            assert gene.strain_id == strain.id
            assert gene.strain == strain.isolate_name

    @pytest.mark.asyncio
    async def test_get_genes_by_multiple_genomes(self):
        strain1 = await sync_to_async(StrainFactory.create)()
        strain2 = await sync_to_async(StrainFactory.create)()
        await sync_to_async(GeneFactory.create_batch)(2, strain=strain1)
        await sync_to_async(GeneFactory.create_batch)(2, strain=strain2)

        service = GeneService()
        result = await service.get_genes_by_multiple_genomes(genome_ids=[strain1.id, strain2.id])

        assert len(result.results) == 4
        strain_ids_in_results = {gene.strain_id for gene in result.results}
        assert strain1.id in strain_ids_in_results
        assert strain2.id in strain_ids_in_results

    @pytest.mark.asyncio
    async def test_autocomplete_gene_suggestions(self):
        # Create only two genes that should match
        await sync_to_async(GeneFactory.create_batch)(
            2, gene_name=factory.Iterator(["geneXX", "geneXY"])
        )
        # another gene that should NOT match
        await sync_to_async(GeneFactory.create)(gene_name="otherGene")

        service = GeneService()
        result = await service.autocomplete_gene_suggestions(query="geneX")

        assert len(result) == 2  # Expect only "geneXX" and "geneXY" to match
        assert all("gene" in gene[GENE_FIELD_NAME] for gene in result)

    @pytest.mark.asyncio
    async def test_get_essentiality_data_by_strain_and_ref(self):
        strain = await sync_to_async(StrainFactory.create)()
        gene = await sync_to_async(GeneFactory.create)(strain=strain)
        essentiality_tag = await sync_to_async(EssentialityTagFactory.create)(name="Essential")
        await sync_to_async(GeneEssentiality.objects.create)(
            gene=gene,
            media="solid",
            essentiality=essentiality_tag,
        )

        service = GeneService()
        await service.load_essentiality_data_by_strain()
        result = await service.get_essentiality_data_by_strain_and_ref(
            strain_id=strain.id, ref_name=gene.seq_id
        )

        assert gene.locus_tag in result

    @pytest.mark.asyncio
    async def test_load_essentiality_data_by_strain(self):
        strain = await sync_to_async(StrainFactory.create)()
        gene = await sync_to_async(GeneFactory.create)(strain=strain)
        essentiality_tag = await sync_to_async(EssentialityTagFactory.create)(name="Essential")
        await sync_to_async(GeneEssentiality.objects.create)(
            gene=gene,
            media="solid",
            essentiality=essentiality_tag,
        )

        service = GeneService()
        result = await service.load_essentiality_data_by_strain()

        assert strain.id in result
