import logging
from typing import List, Optional

from asgiref.sync import sync_to_async
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Router
from ninja.errors import HttpError
from pydantic import BaseModel

from .models import Species
from .models import Strain, Gene
from .services import SearchService
from .utils import construct_file_urls

logger = logging.getLogger(__name__)

api = NinjaAPI(
    title="ME TT DataPortal Data Portal API",
    description="API for genome browser and contextual information.",
    urls_namespace="api",
    csrf=True,
)

search_router = Router()


# Define response schemas
class SearchGenomeSchema(BaseModel):
    species: str
    id: int
    common_name: Optional[str]
    isolate_name: str
    assembly_name: Optional[str]
    assembly_accession: Optional[str]
    fasta_file: str
    gff_file: str


class PaginationSchema(BaseModel):
    results: List[SearchGenomeSchema]
    page_number: int
    num_pages: int
    has_previous: bool
    has_next: bool
    total_results: int


class JBrowseResponseSchema(BaseModel):
    species: str
    isolate_name: str
    fasta_url: str
    gff_url: str
    fasta_file_name: str
    gff_file_name: str


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
                return PaginationSchema(
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
                }
                for strain in full_results
            ])()

            total_results = len(results)
            start = (page - 1) * per_page
            end = start + per_page
            page_results = results[start:end]

            return PaginationSchema(
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


# JBrowseAPI class to handle JBrowse related endpoints
class JBrowseAPI:
    @staticmethod
    def get_jbrowse_data(isolate_id: int):
        strain = get_object_or_404(Strain, id=isolate_id)
        fasta_url, gff_url, fasta_file_name, gff_file_name = construct_file_urls(strain)

        return JBrowseResponseSchema(
            species=strain.species.scientific_name,
            isolate_name=strain.isolate_name,
            fasta_url=fasta_url,
            gff_url=gff_url,
            fasta_file_name=fasta_file_name,
            gff_file_name=gff_file_name
        )


# Instantiate SearchAPI and JBrowseAPI
search_service = SearchService()
search_api = SearchAPI(search_service)
jbrowse_api = JBrowseAPI()


# Map the router to the class methods
@search_router.get('/autocomplete')
async def autocomplete_suggestions(request, query: str, limit: int = 10, species_id: Optional[int] = None):
    # Convert species_id to None if it's an empty string
    if species_id == '' or species_id is None:
        species_id = None
    else:
        try:
            species_id = int(species_id)
        except ValueError:
            species_id = None

    logger.info(f'species_id={species_id}')
    return await search_api.autocomplete_suggestions(query, limit, species_id)


@search_router.get('/strains/{strain_id}/genes/search/')
async def search_genes_in_strain(request, strain_id: int, q: str):
    return await search_api.search_genes_in_strain(strain_id, q)


@search_router.get('/genes/search/')
def search_genes_globally(request, q: str):
    return search_api.search_genes_globally(q)


@search_router.get('/strains-genes/search/')
def search_genes_in_strains(request, strain_q: str, gene_q: str):
    return search_api.search_genes_in_strains(strain_q, gene_q)


@search_router.get('/genome')
async def search_results(request, query: Optional[str] = None, isolate_name: Optional[str] = None,
                         strain_id: Optional[int] = None, gene_id: Optional[int] = None,
                         sortField: Optional[str] = '', sortOrder: Optional[str] = '',
                         page: int = 1, per_page: int = 10):
    return await search_api.search_results(query=query, isolate_name=isolate_name, strain_id=strain_id, gene_id=gene_id,
                                           sortField=sortField, sortOrder=sortOrder, page=page, per_page=per_page)


species_router = Router()


@species_router.get("/list", response=List[SpeciesOut])
def get_species_list(request):
    species = Species.objects.all()
    # Convert the queryset into a list of SpeciesOut Pydantic models
    return [SpeciesOut.from_orm(sp) for sp in species]


@search_router.get('/jbrowse/{isolate_id}')
def get_jbrowse_data(request, isolate_id: int):
    return jbrowse_api.get_jbrowse_data(isolate_id)


api.add_router("/search", search_router)

# Add the species router to the main API
api.add_router("/species", species_router)
