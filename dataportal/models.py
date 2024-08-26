import logging

import aiosqlite
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


class SpeciesManager(models.Manager):
    async def search_species(self, query, sort_field='', sort_order=''):
        database_path = settings.DATABASES['default']['NAME']
        wildcard_query = f'"{query}"*'

        SORT_FIELD_MAP = {
            'species': 'scientific_name',
            'common_name': 'common_name',
            'isolate_name': 'isolate_name',
            'strain_name': 'strain_name',
            'assembly_name': 'assembly_name',
        }

        db_sort_field = SORT_FIELD_MAP.get(sort_field, sort_field)

        async with aiosqlite.connect(database_path) as db:
            species_match_query = """
            SELECT rowid FROM species_fts WHERE species_fts MATCH ?
            """
            strain_match_query = """
            SELECT rowid FROM strain_fts WHERE strain_fts MATCH ?
            """
            gene_match_query = """
            SELECT rowid FROM gene_fts WHERE gene_fts MATCH ?
            """

            species_ids, strain_ids, gene_ids = [], [], []

            async with db.execute(species_match_query, (wildcard_query,)) as cursor:
                async for row in cursor:
                    species_ids.append(row[0])

            async with db.execute(strain_match_query, (wildcard_query,)) as cursor:
                async for row in cursor:
                    strain_ids.append(row[0])

            async with db.execute(gene_match_query, (wildcard_query,)) as cursor:
                async for row in cursor:
                    gene_ids.append(row[0])

            query_string = f"""
            SELECT DISTINCT
                st.id,  -- Include the strain ID in the selection
                s.scientific_name,
                s.common_name,
                st.isolate_name,
                st.strain_name,
                st.assembly_name,
                st.assembly_accession,
                st.fasta_file,
                st.gff_file
            FROM
                species s
            JOIN
                strain st ON s.id = st.species_id
            WHERE
                s.rowid IN ({','.join('?' * len(species_ids))})
                OR st.rowid IN ({','.join('?' * len(strain_ids))})
                OR st.species_id IN (SELECT id FROM species WHERE rowid IN ({','.join('?' * len(species_ids))}))
                OR st.rowid IN (SELECT strain_id FROM gene WHERE rowid IN ({','.join('?' * len(gene_ids))}))
            """

            if db_sort_field and sort_order:
                query_string += f" ORDER BY {db_sort_field} {sort_order.upper()}"

            all_results = []
            async with db.execute(query_string, (*species_ids, *strain_ids, *species_ids, *gene_ids)) as cursor:
                async for row in cursor:
                    print(f'id: {row[0]}')  # Adjusted index to match updated SELECT statement
                    isolate_name = row[3]  # Adjusted index to match updated SELECT statement
                    all_results.append({
                        'id': row[0],  # Add the ID to the results
                        'species': row[1],
                        'common_name': row[2],
                        'isolate_name': row[3],
                        'strain_name': row[4],
                        'assembly_name': row[5],
                        'assembly_accession': row[6],
                        'fasta_file': settings.ASSEMBLY_FTP_PATH + row[7],
                        'gff_file': settings.GFF_FTP_PATH.format(isolate_name) + row[8]
                    })

            return all_results

    async def autocomplete_suggestions(self, query, limit=10):
        database_path = settings.DATABASES['default']['NAME']
        wildcard_query = f'"{query}"*'

        try:
            async with aiosqlite.connect(database_path) as db:
                suggestions = []

                # Autocomplete for species
                species_query = f"""
                SELECT
                    DISTINCT s.scientific_name,
                    s.common_name
                FROM
                    species s
                JOIN 
                    species_fts fts ON s.rowid = fts.rowid
                WHERE
                    species_fts MATCH ?
                LIMIT ?
                """
                async with db.execute(species_query, (wildcard_query, limit)) as cursor:
                    async for row in cursor:
                        suggestions.append(f"{row[0]} ({row[1]})")

                # Autocomplete for strains
                strain_query = f"""
                SELECT
                    DISTINCT st.isolate_name,
                    st.strain_name,
                    st.assembly_name
                FROM
                    strain st
                JOIN 
                    strain_fts fts ON st.rowid = fts.rowid
                JOIN 
                    species s ON st.species_id = s.id
                WHERE
                    strain_fts MATCH ?
                AND 
                    s.scientific_name IS NOT NULL
                LIMIT ?
                """
                async with db.execute(strain_query, (wildcard_query, limit)) as cursor:
                    async for row in cursor:
                        suggestions.append(f"{row[0]} - {row[1]} ({row[2]})")

                # Autocomplete for genes
                gene_query = f"""
                SELECT
                    DISTINCT g.gene_name,
                    g.gene_symbol
                FROM
                    gene g
                JOIN 
                    gene_fts fts ON g.rowid = fts.rowid
                JOIN 
                    strain st ON g.strain_id = st.id
                JOIN 
                    species s ON st.species_id = s.id
                WHERE
                    gene_fts MATCH ?
                AND 
                    s.scientific_name IS NOT NULL
                AND 
                    st.strain_name IS NOT NULL
                LIMIT ?
                """
                async with db.execute(gene_query, (wildcard_query, limit)) as cursor:
                    async for row in cursor:
                        suggestions.append(f"{row[0]} ({row[1]})")

                return suggestions

        except Exception as e:
            logger.error(f"Error executing autocomplete query: {e}")
            return []


class Species(models.Model):
    id = models.AutoField(primary_key=True)  # Primary key, auto-incrementing ID
    scientific_name = models.CharField(max_length=255)
    common_name = models.CharField(max_length=255, blank=True, null=True)
    taxonomy_id = models.IntegerField(unique=True)  # Unique taxonomy ID

    objects = SpeciesManager()

    class Meta:
        db_table = 'species'

    def __str__(self):
        return self.scientific_name


class Strain(models.Model):
    id = models.AutoField(primary_key=True)  # Primary key, auto-incrementing ID
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name='strains')
    isolate_name = models.CharField(max_length=255)
    strain_name = models.CharField(max_length=255, blank=True, null=True)
    assembly_name = models.CharField(max_length=255, blank=True, null=True)
    assembly_accession = models.CharField(max_length=255, blank=True, null=True)
    fasta_file = models.CharField(max_length=255)
    gff_file = models.CharField(max_length=255)

    class Meta:
        db_table = 'strain'

    def __str__(self):
        return f"{self.isolate_name} ({self.strain_name})"


class Gene(models.Model):
    id = models.AutoField(primary_key=True)  # Primary key, auto-incrementing ID
    strain = models.ForeignKey(Strain, on_delete=models.CASCADE, related_name='genes')
    gene_id = models.CharField(max_length=255)
    gene_name = models.CharField(max_length=255, blank=True, null=True)
    gene_symbol = models.CharField(max_length=255, blank=True, null=True)
    locus_tag = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'gene'

    def __str__(self):
        return self.gene_name or self.gene_id
