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

    query_string = f"SELECT * FROM speciesdata_fts WHERE speciesdata_fts MATCH ? {sort_clause}"
    logger.debug(f"Executing query: {query_string} with wildcard_query: {wildcard_query}")

    try:
        async with aiosqlite.connect(database_path) as db:
            async with db.execute(query_string, (wildcard_query,)) as cursor:
                all_results = []
                async for row in cursor:
                    isolate_name = row[1]
                    all_results.append({
                        'species': row[0],
                        'isolate_name': isolate_name,
                        'assembly_name': row[2],
                        'fasta_file': settings.ASSEMBLY_FTP_PATH + row[3],
                        'gff_file': settings.GFF_FTP_PATH.format(isolate_name) + row[4]
                    })

        total_results = len(all_results)
        start = (page - 1) * per_page
        end = start + per_page
        page_results = all_results[start:end]

        return total_results, page_results

    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise

    return 0, []
