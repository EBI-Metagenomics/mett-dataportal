import aiosqlite
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


async def search_species_data(query, sort_field='', sort_order='', page=1, per_page=10):
    database_path = settings.DATABASES['default']['NAME']
    results = []
    sort_clause = ''
    wildcard_query = f'"{query}"*'

    if sort_field and sort_order:
        sort_clause = f"ORDER BY {sort_field} {sort_order.upper()}"

    try:
        logger.debug(f"Connecting to the database at: {database_path}")
        async with aiosqlite.connect(database_path) as db:
            logger.debug("Connected to the database successfully.")

            # Step 1: Get the rowids of species, strain, and gene based on FTS search
            species_match_query = """
            SELECT rowid FROM species_fts WHERE species_fts MATCH ?
            """
            strain_match_query = """
            SELECT rowid FROM strain_fts WHERE strain_fts MATCH ?
            """
            gene_match_query = """
            SELECT rowid FROM gene_fts WHERE gene_fts MATCH ?
            """

            species_ids = []
            strain_ids = []
            gene_ids = []

            async with db.execute(species_match_query, (wildcard_query,)) as cursor:
                async for row in cursor:
                    species_ids.append(row[0])

            async with db.execute(strain_match_query, (wildcard_query,)) as cursor:
                async for row in cursor:
                    strain_ids.append(row[0])

            async with db.execute(gene_match_query, (wildcard_query,)) as cursor:
                async for row in cursor:
                    gene_ids.append(row[0])

            # Step 2: Now perform the main query using the obtained rowids but without retrieving gene information
            # and include all strains linked to matched species
            query_string = f"""
            SELECT DISTINCT
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
            {sort_clause}
            """
            logger.debug(
                f"Executing query: {query_string} with species_ids: {species_ids}, strain_ids: {strain_ids}, gene_ids: {gene_ids}")

            all_results = []
            async with db.execute(query_string, (*species_ids, *strain_ids, *species_ids, *gene_ids)) as cursor:
                async for row in cursor:
                    logger.debug(f"Processing row: {row}")
                    all_results.append({
                        'species': row[0],
                        'common_name': row[1],
                        'isolate_name': row[2],
                        'strain_name': row[3],
                        'assembly_name': row[4],
                        'assembly_accession': row[5],
                        'fasta_file': settings.ASSEMBLY_FTP_PATH + row[6],
                        'gff_file': settings.GFF_FTP_PATH.format(row[2]) + row[7],
                    })

            logger.debug(f"Total rows retrieved: {len(all_results)}")

            # Paginate the results
            total_results = len(all_results)
            start = (page - 1) * per_page
            end = start + per_page
            page_results = all_results[start:end]

            logger.debug(f"Returning {len(page_results)} results for page {page}.")

            return total_results, page_results

    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise

    return 0, []


async def autocomplete_suggestions(query, limit=10):
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
