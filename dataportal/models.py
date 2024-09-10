import logging

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db import models

logger = logging.getLogger(__name__)


class SpeciesManager(models.Manager):
    def search_species(self, query, sort_field='', sort_order=''):
        SORT_FIELD_MAP = {
            'species': 'scientific_name',
            'common_name': 'common_name',
            'isolate_name': 'isolate_name',
            'strain_name': 'strain_name',
            'assembly_name': 'assembly_name',
        }

        db_sort_field = SORT_FIELD_MAP.get(sort_field, sort_field)

        search_vector = SearchVector('scientific_name', 'common_name', 'strain__strain_name', 'strain__assembly_name')
        search_query = SearchQuery(query)

        query_set = self.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query)

        if db_sort_field and sort_order:
            query_set = query_set.order_by(f"{db_sort_field} {sort_order.upper()}")

        return query_set

    def autocomplete_suggestions(self, query, limit=10):
        search_vector = SearchVector('scientific_name', 'common_name')
        search_query = SearchQuery(query)

        return self.annotate(
            search=search_vector
        ).filter(search=search_query)[:limit]


from django.db import models
from django.contrib.postgres.indexes import GinIndex


# Species Model
class Species(models.Model):
    id = models.AutoField(primary_key=True)
    scientific_name = models.CharField(max_length=255, db_index=True)  # Indexed for search
    common_name = models.CharField(max_length=255, blank=True, null=True)
    acronym = models.CharField(max_length=10, blank=True, null=True)  # New column for acronym
    taxonomy_id = models.IntegerField(unique=True)

    objects = models.Manager()

    class Meta:
        db_table = 'species'
        indexes = [
            GinIndex(fields=['scientific_name'], name='species_sci_name_gin_idx', opclasses=['gin_trgm_ops']),
        ]

    def __str__(self):
        return self.scientific_name


# Strain Model
class Strain(models.Model):
    id = models.AutoField(primary_key=True)
    species = models.ForeignKey('Species', on_delete=models.CASCADE, related_name='strains')
    isolate_name = models.CharField(max_length=255)
    assembly_name = models.CharField(max_length=255, blank=True, null=True)
    assembly_accession = models.CharField(max_length=20, unique=True, blank=True, null=True)
    fasta_file = models.CharField(max_length=255)
    gff_file = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'strain'
        indexes = [
            GinIndex(fields=['isolate_name'], name='isolate_name_gin_idx', opclasses=['gin_trgm_ops']),
        ]

    def __str__(self):
        return f"{self.isolate_name}"


# Gene Model (with JSONB annotations storing multiple records)
class Gene(models.Model):
    id = models.AutoField(primary_key=True)
    strain = models.ForeignKey('Strain', on_delete=models.CASCADE, related_name='genes')
    gene_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # Optional gene name
    locus_tag = models.CharField(max_length=255, unique=True, db_index=True)  # Ensure locus_tag is unique
    description = models.TextField(blank=True, null=True)
    annotations = models.JSONField(blank=True, null=True)  # Store flexible annotations

    class Meta:
        db_table = 'gene'
        indexes = [
            GinIndex(fields=['gene_name'], name='gene_name_gin_idx', opclasses=['gin_trgm_ops']),
            GinIndex(fields=['locus_tag'], name='locus_tag_gin_idx', opclasses=['gin_trgm_ops']),  # Index locus_tag
            GinIndex(fields=['annotations'], name='gene_annotations_gin_idx', opclasses=['jsonb_path_ops']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['locus_tag'], name='unique_locus_tag'),  # Unique constraint for locus_tag
        ]

    def __str__(self):
        return self.gene_name or self.locus_tag


# GeneOntologyTerm Model (for storing gene ontology data)
class GeneOntologyTerm(models.Model):
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE, related_name='ontology_terms')
    ontology_type = models.CharField(max_length=50)  # e.g., "GO"
    ontology_id = models.CharField(max_length=255)
    ontology_description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'gene_ontology_term'
        indexes = [
            GinIndex(fields=['ontology_id', 'ontology_description'], name='go_term_id_desc_gin_idx',
                     opclasses=['gin_trgm_ops', 'gin_trgm_ops']),
        ]

    def __str__(self):
        return f"{self.ontology_type} - {self.ontology_id}"


# CrossReferences Model (for external references like UniProt, Pfam, etc.)
class CrossReferences(models.Model):
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE, related_name='cross_references')
    db_name = models.CharField(max_length=255)  # Name of the external database
    db_accession = models.CharField(max_length=255)  # Accession number in the external database
    db_description = models.TextField()

    class Meta:
        db_table = 'cross_references'
        indexes = [
            GinIndex(fields=['db_name', 'db_accession', 'db_description'], name='cross_refs_db_acc_desc_gin_idx',
                     opclasses=['gin_trgm_ops', 'gin_trgm_ops', 'gin_trgm_ops']),
        ]

    def __str__(self):
        return f"{self.db_name} - {self.db_accession}"


# ReferenceGeneDescription Model (for storing reference gene descriptions like RefSeq, Ensembl, etc.)
class ReferenceGeneDescription(models.Model):
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE, related_name='reference_descriptions')
    reference_source = models.CharField(max_length=255)  # e.g., "RefSeq", "Ensembl"
    description = models.TextField()

    class Meta:
        db_table = 'reference_gene_description'
        indexes = [
            GinIndex(fields=['reference_source', 'description'], name='ref_gene_src_desc_gin_idx',
                     opclasses=['gin_trgm_ops', 'gin_trgm_ops']),
        ]

    def __str__(self):
        return f"{self.reference_source} - Description for {self.gene.gene_name}"
