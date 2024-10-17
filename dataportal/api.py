import logging
from typing import List, Optional

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Router
from ninja.errors import HttpError
from pydantic import BaseModel

from .models import Species
from .models import Strain, Gene
from .services import SearchService

logger = logging.getLogger(__name__)

api = NinjaAPI(
    title="ME TT DataPortal Data Portal API",
    description="API for genome browser and contextual information.",
    urls_namespace="api",
    csrf=True,
)

genome_router = Router(tags=["Genomes"])
gene_router = Router(tags=["Genes"])
species_router = Router(tags=["Species"])
jbrowse_router = Router(tags=["JBrowse Viewer"])


# Define response schemas

class StrainSuggestionSchema(BaseModel):
    strain_id: int
    isolate_name: str
    assembly_name: str


class GeneAutocompleteResponseSchema(BaseModel):
    gene_id: int
    gene_name: Optional[str]
    strain_name: str


class ContigSchema(BaseModel):
    seq_id: str
    length: Optional[int] = None


class SearchGenomeSchema(BaseModel):
    species: str
    id: int
    common_name: Optional[str]
    isolate_name: str
    assembly_name: Optional[str]
    assembly_accession: Optional[str]
    fasta_file: str
    gff_file: str
    fasta_url: str
    gff_url: str
    contigs: List[ContigSchema]


class TypeStrainSchema(BaseModel):
    id: int
    isolate_name: str
    assembly_name: Optional[str]
    assembly_accession: Optional[str]
    fasta_file: str
    gff_file: str
    fasta_url: str
    gff_url: str


class GeneResponseSchema(BaseModel):
    id: int
    seq_id: Optional[str] = None
    gene_name: Optional[str] = None
    description: Optional[str] = None
    strain_id: Optional[int] = None
    strain: Optional[str] = None
    assembly: Optional[str] = None
    locus_tag: Optional[str] = None
    cog: Optional[str] = None
    kegg: Optional[str] = None
    pfam: Optional[str] = None
    interpro: Optional[str] = None
    dbxref: Optional[str] = None
    ec_number: Optional[str] = None
    product: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    annotations: Optional[dict] = None


class GenomePaginationSchema(BaseModel):
    results: List[SearchGenomeSchema]
    page_number: int
    num_pages: int
    has_previous: bool
    has_next: bool
    total_results: int


class GenePaginationSchema(BaseModel):
    results: List[GeneResponseSchema]
    page_number: int
    num_pages: int
    has_previous: bool
    has_next: bool
    total_results: int


class SpeciesOut(BaseModel):
    id: int
    scientific_name: str
    common_name: str
    acronym: str

    class Config:
        from_attributes = True


# SearchAPI class to handle search-related endpoints
class SearchAPI:
    def __init__(self, search_service: SearchService):
        self.search_service = search_service

    async def autocomplete_suggestions(self, query: str, limit: int = 10, species_id: Optional[int] = None):
        try:
            suggestions = await self.search_service.search_strains(query, limit, species_id)
            return suggestions
        except Exception as e:
            raise HttpError(500, f"Error occurred: {str(e)}")

    async def gene_autocomplete(self, query: str, limit: int = 10, species_id: Optional[int] = None,
                                genome_ids: Optional[str] = None):
        try:
            genome_id_list = [int(gid) for gid in genome_ids.split(",") if gid.strip()] if genome_ids else None

            suggestions = await self.search_service.autocomplete_gene_suggestions(query, limit, species_id,
                                                                                  genome_id_list)
            return suggestions

        except Exception as e:
            logger.error(f"Error in gene_autocomplete: {e}")
            raise HttpError(500, "Internal Server Error")

    async def search_genes_in_strain(self, strain_id: int, q: str):
        try:
            strain = await sync_to_async(lambda: get_object_or_404(Strain, id=strain_id))()
            gene_query = await sync_to_async(lambda: list(
                Gene.objects.filter(
                    strain=strain,
                    gene_name__icontains=q
                )[:10]
            ))()
            return [{"gene_name": gene.gene_name, "description": gene.description} for gene in gene_query]
        except HttpError as e:
            raise e
        except Exception as e:
            logger.error(f"Error in search_genes_in_strain: {e}")
            raise HttpError(500, f"Error occurred: {str(e)}")

    def search_genes_globally(self, q: str):
        if not q.strip():
            raise HttpError(400, "Query parameter 'q' cannot be empty")

        try:
            genes = self.search_service.search_genes_globally(q)
            return [{"gene_name": g.gene_name, "strain": g.strain.isolate_name, "assembly": g.strain.assembly_name,
                     "description": g.description} for g in genes]
        except Exception as e:
            return {'error': str(e)}, 500

    def search_genes_in_strains(self, strain_q: str, gene_q: str):
        try:
            genes = self.search_service.search_genes_in_strains(strain_q, gene_q)

            if not genes:
                raise HttpError(404, f"No genes found matching '{gene_q}' in strains matching '{strain_q}'")

            return [{"gene_name": g.gene_name, "strain": g.strain.isolate_name, "assembly": g.strain.assembly_name,
                     "description": g.description} for g in genes]
        except HttpError as e:
            raise e
        except Exception as e:
            return {'error': str(e)}, 500

    async def search_results(self, query: Optional[str] = None, isolate_name: Optional[str] = None,
                             strain_id: Optional[int] = None, gene_id: Optional[int] = None,
                             sortField: Optional[str] = '', sortOrder: Optional[str] = '',
                             page: int = 1, per_page: int = 10):
        try:
            logger.debug(f"query: {query}, isolate_name: {isolate_name}, strain_id: {strain_id}, gene_id: {gene_id}")

            if gene_id:
                full_results = await self.search_service.search_genome_by_gene(gene_id=gene_id)
            elif strain_id:
                full_results = await self.search_service.search_genomes(strain_id=strain_id)
            else:
                search_term = isolate_name or query
                full_results = await self.search_service.search_genomes(query=search_term)

            if not full_results:
                return GenomePaginationSchema(
                    results=[],
                    page_number=1,
                    num_pages=0,
                    has_previous=False,
                    has_next=False,
                    total_results=0,
                )

            results = await sync_to_async(lambda: [
                {
                    "species": strain.species.scientific_name,
                    "id": strain.id,
                    "common_name": strain.species.common_name if strain.species.common_name else None,
                    "isolate_name": strain.isolate_name,
                    "assembly_name": strain.assembly_name,
                    "assembly_accession": strain.assembly_accession,
                    "fasta_file": strain.fasta_file,
                    "gff_file": strain.gff_file,
                    "fasta_url": f"{settings.ASSEMBLY_FTP_PATH}{strain.assembly_name}/{strain.fasta_file}",
                    "gff_url": settings.GFF_FTP_PATH.format(strain.isolate_name) + strain.gff_file,
                }
                for strain in full_results
            ])()

            total_results = len(results)
            start = (page - 1) * per_page
            end = start + per_page
            page_results = results[start:end]

            return GenomePaginationSchema(
                results=page_results,
                page_number=page,
                num_pages=(total_results + per_page - 1) // per_page,
                has_previous=page > 1,
                has_next=end < total_results,
                total_results=total_results,
            )
        except Exception as e:
            logger.error(f"Error in search_results: {e}")
            raise HttpError(500, f"Internal Server Error: {str(e)}")


# Instantiate SearchAPI and JBrowseAPI
search_service = SearchService()
search_api = SearchAPI(search_service)


# Map the router to the class methods
@genome_router.get('/autocomplete', response=List[StrainSuggestionSchema])
async def autocomplete_suggestions(request, query: str, limit: int = 10, species_id: Optional[int] = None):
    return await search_service.search_strains(query, limit, species_id)


# API Endpoint to retrieve all species
@species_router.get("/", response=List[SpeciesOut])
def get_all_species(request):
    species = Species.objects.all()
    return [SpeciesOut.from_orm(sp) for sp in species]


from asgiref.sync import sync_to_async


# API Endpoint to retrieve all genomes
@genome_router.get("/", response=GenomePaginationSchema)
async def get_all_genomes(request, page: int = 1, per_page: int = 10):
    try:
        # Use sync_to_async to make this query non-blocking in the async context
        strains = await sync_to_async(lambda: list(Strain.objects.select_related('species').all()))()

        total_results = len(strains)
        start = (page - 1) * per_page
        end = start + per_page
        page_results = strains[start:end]

        # Initialize the results list
        serialized_results = []

        # Loop through strains and fetch contigs asynchronously
        for strain in page_results:
            contigs = await sync_to_async(lambda: list(strain.contigs.all()))()
            serialized_contigs = [{"seq_id": contig.seq_id, "length": contig.length} for contig in contigs]

            serialized_results.append({
                "species": strain.species.scientific_name,
                "id": strain.id,
                "common_name": strain.species.common_name if strain.species.common_name else None,
                "isolate_name": strain.isolate_name,
                "assembly_name": strain.assembly_name,
                "assembly_accession": strain.assembly_accession if strain.assembly_accession else None,
                "fasta_file": strain.fasta_file,
                "gff_file": strain.gff_file,
                "fasta_url": f"{settings.ASSEMBLY_FTP_PATH}{strain.assembly_name}/{strain.fasta_file}",
                "gff_url": f"{settings.GFF_FTP_PATH.format(strain.isolate_name)}{strain.gff_file}",
                "contigs": serialized_contigs
            })

        return GenomePaginationSchema(
            results=serialized_results,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=end < total_results,
            total_results=total_results,
        )
    except Exception as e:
        logger.error(f"Error in get_all_genomes: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# API Endpoint to search genomes by query string
@genome_router.get("/type-strains", response=List[TypeStrainSchema])
async def get_type_strains(request):
    # Initialize the results list
    serialized_results = []
    try:
        # Properly wrap the ORM call using sync_to_async and await it
        strains = await sync_to_async(list)(Strain.objects.filter(type_strain=True))

        for strain in strains:
            serialized_results.append({
                "id": strain.id,
                "isolate_name": strain.isolate_name,
                "assembly_name": strain.assembly_name,
                "assembly_accession": strain.assembly_accession if strain.assembly_accession else None,
                "fasta_file": strain.fasta_file,
                "gff_file": strain.gff_file,
                "fasta_url": f"{settings.ASSEMBLY_FTP_PATH}{strain.assembly_name}/{strain.fasta_file}",
                "gff_url": settings.GFF_FTP_PATH.format(strain.isolate_name) + strain.gff_file
            })
        return serialized_results
    except Exception as e:
        raise HttpError(500, f"An error occurred: {str(e)}")


@genome_router.get("/search", response=GenomePaginationSchema)
async def search_genomes_by_string(request, query: str, page: int = 1, per_page: int = 10):
    try:
        # Fetch strains asynchronously
        strains = await sync_to_async(lambda: list(Strain.objects.select_related('species')
                                                   .filter(isolate_name__icontains=query)))()

        total_results = len(strains)
        start = (page - 1) * per_page
        end = start + per_page
        page_results = strains[start:end]

        # Initialize the results list
        serialized_results = []

        # Fetch contigs asynchronously for each strain
        for strain in strains:
            contigs = await sync_to_async(lambda: list(strain.contigs.all()))()  # Fetch contigs asynchronously
            serialized_contigs = [{"seq_id": contig.seq_id, "length": contig.length} for contig in contigs]

            serialized_results.append({
                "species": strain.species.scientific_name,
                "id": strain.id,
                "common_name": strain.species.common_name if strain.species.common_name else None,
                "isolate_name": strain.isolate_name,
                "assembly_name": strain.assembly_name,
                "assembly_accession": strain.assembly_accession if strain.assembly_accession else None,
                "fasta_file": strain.fasta_file or "",
                "gff_file": strain.gff_file or "",
                "fasta_url": f"{settings.ASSEMBLY_FTP_PATH}{strain.assembly_name}/{strain.fasta_file}" if strain.fasta_file else "",
                "gff_url": f"{settings.GFF_FTP_PATH.format(strain.isolate_name)}{strain.gff_file}" if strain.gff_file else "",
                "contigs": serialized_contigs  # Include contig data in the response
            })

        return GenomePaginationSchema(
            results=serialized_results,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=end < total_results,
            total_results=total_results,
        )

    except Exception as e:
        logger.error(f"Error in search_genomes_by_string: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# API Endpoint to retrieve genome by ID
@genome_router.get("/{genome_id}", response=SearchGenomeSchema)
def get_genome(request, genome_id: int):
    try:
        strain = Strain.objects.select_related('species').get(id=genome_id)
        response_data = {
            "id": strain.id,
            "species": strain.species.scientific_name,
            "common_name": strain.species.common_name if strain.species.common_name else None,
            "isolate_name": strain.isolate_name,
            "assembly_name": strain.assembly_name,
            "assembly_accession": strain.assembly_accession if strain.assembly_accession else None,
            "fasta_file": strain.fasta_file,
            "gff_file": strain.gff_file,
            "fasta_url": f"{settings.ASSEMBLY_FTP_PATH}{strain.assembly_name}/{strain.fasta_file}",
            "gff_url": settings.GFF_FTP_PATH.format(strain.isolate_name) + strain.gff_file,
            "contigs": [
                {"seq_id": contig.seq_id, "length": contig.length}
                for contig in strain.contigs.all()  # Fetch related contigs
            ]
        }
        return response_data
    except Strain.DoesNotExist:
        raise HttpError(404, "Genome not found")


# API Endpoint to retrieve genomes filtered by species ID
@species_router.get("/{species_id}/genomes", response=GenomePaginationSchema)
async def get_genomes_by_species(request, species_id: int, page: int = 1, per_page: int = 10):
    try:
        # Fetch strains asynchronously
        strains = await sync_to_async(lambda: list(Strain.objects.select_related('species')
                                                   .filter(species_id=species_id)))()

        total_results = len(strains)
        start = (page - 1) * per_page
        end = start + per_page
        page_results = strains[start:end]

        # Initialize the results list
        serialized_results = []

        # Fetch contigs asynchronously for each strain
        for strain in page_results:
            contigs = await sync_to_async(lambda: list(strain.contigs.all()))()  # Fetch contigs asynchronously
            serialized_contigs = [{"seq_id": contig.seq_id, "length": contig.length} for contig in contigs]

            serialized_results.append({
                "species": strain.species.scientific_name,
                "id": strain.id,
                "common_name": strain.species.common_name if strain.species.common_name else None,
                "isolate_name": strain.isolate_name,
                "assembly_name": strain.assembly_name,
                "assembly_accession": strain.assembly_accession if strain.assembly_accession else None,
                "fasta_file": strain.fasta_file or "",  # Ensure fasta_file is not None
                "gff_file": strain.gff_file or "",  # Ensure gff_file is not None
                "fasta_url": f"{settings.ASSEMBLY_FTP_PATH}{strain.assembly_name}/{strain.fasta_file}" if strain.fasta_file else "",
                "gff_url": f"{settings.GFF_FTP_PATH.format(strain.isolate_name)}{strain.gff_file}" if strain.gff_file else "",
                "contigs": serialized_contigs  # Include contig data in the response
            })

        return GenomePaginationSchema(
            results=serialized_results,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=end < total_results,
            total_results=total_results,
        )

    except Exception as e:
        logger.error(f"Error in get_genomes_by_species: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# API Endpoint to search genomes by species ID and query string
@species_router.get("/{species_id}/genomes/search", response=GenomePaginationSchema)
async def search_genomes_by_species_and_string(request, species_id: int, query: str, page: int = 1, per_page: int = 10):
    try:
        # Fetch strains asynchronously
        strains = await sync_to_async(lambda: list(Strain.objects.select_related('species')
                                                   .filter(species_id=species_id, isolate_name__icontains=query)))()

        total_results = len(strains)
        start = (page - 1) * per_page
        end = start + per_page
        page_results = strains[start:end]

        # Initialize the results list
        serialized_results = []

        # Fetch contigs asynchronously for each strain
        for strain in page_results:
            contigs = await sync_to_async(lambda: list(strain.contigs.all()))()  # Fetch contigs asynchronously
            serialized_contigs = [{"seq_id": contig.seq_id, "length": contig.length} for contig in contigs]

            serialized_results.append({
                "species": strain.species.scientific_name,
                "id": strain.id,
                "common_name": strain.species.common_name if strain.species.common_name else None,
                "isolate_name": strain.isolate_name,
                "assembly_name": strain.assembly_name,
                "assembly_accession": strain.assembly_accession if strain.assembly_accession else None,
                "fasta_file": strain.fasta_file or "",
                "gff_file": strain.gff_file or "",
                "fasta_url": f"{settings.ASSEMBLY_FTP_PATH}{strain.assembly_name}/{strain.fasta_file}" if strain.fasta_file else "",
                "gff_url": f"{settings.GFF_FTP_PATH.format(strain.isolate_name)}{strain.gff_file}" if strain.gff_file else "",
                "contigs": serialized_contigs  # Include fetched contigs
            })

        return GenomePaginationSchema(
            results=serialized_results,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=end < total_results,
            total_results=total_results,
        )
    except Exception as e:
        logger.error(f"Error in search_genomes_by_species_and_string: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


@gene_router.get("/autocomplete", response=List[GeneAutocompleteResponseSchema])
async def gene_autocomplete_suggestions(request, query: str, limit: int = 10, species_id: Optional[int] = None,
                                        genome_ids: Optional[str] = None):
    genome_id_list = [int(gid) for gid in genome_ids.split(",") if gid.strip()] if genome_ids else None
    return await search_service.autocomplete_gene_suggestions(query, limit, species_id, genome_id_list)


# API Endpoint to search genes by query string
@gene_router.get("/search", response=GenePaginationSchema)
async def search_genes_by_string(request, query: str, page: int = 1, per_page: int = 10):
    try:
        paginated_results = await search_service.search_genes(query=query, page=page, per_page=per_page)
        return paginated_results
    except Exception as e:
        logger.error(f"Error in search_genes_by_string: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# API Endpoint to retrieve gene by ID
@gene_router.get("/{gene_id}", response=GeneResponseSchema)
async def get_gene_by_id(request, gene_id: int):
    try:
        gene = await sync_to_async(lambda: get_object_or_404(Gene.objects.select_related('strain'), id=gene_id))()

        response_data = {
            "id": gene.id,
            "seq_id": gene.seq_id,
            "gene_name": gene.gene_name or "N/A",
            "description": gene.description or None,
            "strain_id": gene.strain.id if gene.strain else None,
            "strain": gene.strain.isolate_name if gene.strain else "Unknown",
            "assembly": gene.strain.assembly_name if gene.strain and gene.strain.assembly_name else None,
            "locus_tag": gene.locus_tag or None,
            "cog": gene.cog or None,
            "kegg": gene.kegg or None,
            "pfam": gene.pfam or None,
            "interpro": gene.interpro or None,
            "dbxref": gene.dbxref or None,
            "ec_number": gene.ec_number or None,
            "product": gene.product or None,
            "start_position": gene.start_position or None,
            "end_position": gene.end_position or None,
            "annotations": gene.annotations or {}
        }

        return response_data
    except Http404:
        raise HttpError(404, f"Gene with id {gene_id} not found")
    except Exception as e:
        logger.error(f"Error in get_gene_by_id: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# API Endpoint to retrieve all genes
@gene_router.get("/", response=GenePaginationSchema)
async def get_all_genes(request, page: int = 1, per_page: int = 10):
    try:
        genes = await sync_to_async(lambda: list(Gene.objects.select_related('strain').all()))()

        total_results = len(genes)
        start = (page - 1) * per_page
        end = start + per_page
        page_results = genes[start:end]

        serialized_results = [
            {
                "id": gene.id,
                "seq_id": gene.seq_id,
                "gene_name": gene.gene_name or "N/A",
                "description": gene.description or None,
                "strain_id": gene.strain.id if gene.strain else None,
                "strain": gene.strain.isolate_name if gene.strain else "Unknown",
                "assembly": gene.strain.assembly_name if gene.strain and gene.strain.assembly_name else None,
                "locus_tag": gene.locus_tag or None,
                "cog": gene.cog or None,
                "kegg": gene.kegg or None,
                "pfam": gene.pfam or None,
                "interpro": gene.interpro or None,
                "dbxref": gene.dbxref or None,
                "ec_number": gene.ec_number or None,
                "product": gene.product or None,
                "start_position": gene.start_position or None,
                "end_position": gene.end_position or None,
                "annotations": gene.annotations or {}
            }
            for gene in page_results
        ]

        return GenePaginationSchema(
            results=serialized_results,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=end < total_results,
            total_results=total_results,
        )
    except Exception as e:
        logger.error(f"Error in get_all_genes: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# API Endpoint to retrieve genes filtered by a single genome ID
@genome_router.get("/{genome_id}/genes", response=GenePaginationSchema)
async def get_genes_by_genome(request, genome_id: int, page: int = 1, per_page: int = 10):
    try:
        genes = await sync_to_async(lambda: list(Gene.objects.select_related('strain').filter(strain_id=genome_id)))()

        total_results = len(genes)
        start = (page - 1) * per_page
        end = start + per_page
        page_results = genes[start:end]

        serialized_results = [
            {
                "id": gene.id,
                "seq_id": gene.seq_id,
                "gene_name": gene.gene_name if gene.gene_name else "N/A",  # Handle None values
                "description": gene.description if gene.description else None,
                "locus_tag": gene.locus_tag,
                "strain": gene.strain.isolate_name,
                "assembly": gene.strain.assembly_name if gene.strain.assembly_name else None,
            }
            for gene in page_results
        ]

        return GenePaginationSchema(
            results=serialized_results,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=end < total_results,
            total_results=total_results,
        )
    except Exception as e:
        logger.error(f"Error in get_genes_by_genome: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# API Endpoint to search genes by genome ID and gene string
@genome_router.get("/{genome_id}/genes/search", response=GenePaginationSchema)
async def search_genes_by_genome_and_string(request, genome_id: int, query: str, page: int = 1, per_page: int = 10):
    try:
        genes = await sync_to_async(lambda: list(
            Gene.objects.select_related('strain').filter(strain_id=genome_id, gene_name__icontains=query)
        ))()

        total_results = len(genes)
        start = (page - 1) * per_page
        end = start + per_page
        page_results = genes[start:end]

        serialized_results = [
            {
                "id": gene.id,
                "seq_id": gene.seq_id,
                "gene_name": gene.gene_name or "N/A",
                "description": gene.description or None,
                "strain_id": gene.strain.id if gene.strain else None,
                "strain": gene.strain.isolate_name if gene.strain else "Unknown",
                "assembly": gene.strain.assembly_name if gene.strain and gene.strain.assembly_name else None,
                "locus_tag": gene.locus_tag or None,
                "cog": gene.cog or None,
                "kegg": gene.kegg or None,
                "pfam": gene.pfam or None,
                "interpro": gene.interpro or None,
                "dbxref": gene.dbxref or None,
                "ec_number": gene.ec_number or None,
                "product": gene.product or None,
                "start_position": gene.start_position or None,
                "end_position": gene.end_position or None,
                "annotations": gene.annotations or {}
            }
            for gene in genes
        ]

        return GenePaginationSchema(
            results=serialized_results,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=end < total_results,
            total_results=total_results,
        )
    except Exception as e:
        logger.error(f"Error in search_genes_by_genome_and_string: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# API Endpoint to search genes across multiple genome IDs using a gene string
@gene_router.get("/search/filter", response=GenePaginationSchema)
async def search_genes_by_multiple_genomes_and_species_and_string(request, genome_ids: str = "",
                                                                  species_id: Optional[int] = None,
                                                                  query: str = "", page: int = 1, per_page: int = 10):
    try:
        # Process genome IDs
        genome_id_list = [int(gid) for gid in genome_ids.split(",") if gid.strip()] if genome_ids.strip() else []
        genes_query = Gene.objects.select_related('strain')

        if genome_id_list:
            genes_query = genes_query.filter(strain_id__in=genome_id_list)

        if species_id:
            genes_query = genes_query.filter(strain__species_id=species_id)

        if query.strip():
            genes_query = genes_query.filter(gene_name__icontains=query)

        total_results = await sync_to_async(genes_query.count)()
        start = (page - 1) * per_page
        end = start + per_page

        genes = await sync_to_async(lambda: list(genes_query[start:end]))()

        serialized_results = [
            {
                "id": gene.id,
                "seq_id": gene.seq_id,
                "gene_name": gene.gene_name or "N/A",
                "description": gene.description or None,
                "strain_id": gene.strain.id if gene.strain else None,
                "strain": gene.strain.isolate_name if gene.strain else "Unknown",
                "assembly": gene.strain.assembly_name if gene.strain and gene.strain.assembly_name else None,
                "locus_tag": gene.locus_tag or None,
                "cog": gene.cog or None,
                "kegg": gene.kegg or None,
                "pfam": gene.pfam or None,
                "interpro": gene.interpro or None,
                "dbxref": gene.dbxref or None,
                "ec_number": gene.ec_number or None,
                "product": gene.product or None,
                "start_position": gene.start_position or None,
                "end_position": gene.end_position or None,
                "annotations": gene.annotations or {}
            }
            for gene in genes
        ]

        return GenePaginationSchema(
            results=serialized_results,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=end < total_results,
            total_results=total_results,
        )
    except HttpError as e:
        raise e
    except ValueError:
        logger.error("Invalid genome ID provided")
        raise HttpError(400, "Invalid genome ID provided")
    except Exception as e:
        logger.error(f"Error in search_genes_by_multiple_genomes_and_string: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# Register routers with the main API
api.add_router("/species", species_router)
api.add_router("/genomes", genome_router)
api.add_router("/genes", gene_router)
