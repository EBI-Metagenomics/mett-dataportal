from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q


def construct_file_urls(strain):
    # Construct URLs using environment variables
    fasta_url = f"{settings.ASSEMBLY_FTP_PATH}{strain.assembly_name}/{strain.fasta_file}"
    gff_url = settings.GFF_FTP_PATH.format(strain.isolate_name) + strain.gff_file

    return fasta_url, gff_url, strain.fasta_file, strain.gff_file


def paginate_queryset(queryset, page: int, per_page: int):
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)
    return {
        "results": list(page_obj.object_list),
        "page_number": page_obj.number,
        "num_pages": paginator.num_pages,
        "has_previous": page_obj.has_previous(),
        "has_next": page_obj.has_next(),
        "total_results": paginator.count,
    }

async def fetch_objects(model, filters=None, select_related=None, limit=None):
    filters = filters or Q()
    queryset = model.objects.filter(filters)

    if select_related:
        queryset = queryset.select_related(*select_related)

    if limit:
        queryset = queryset[:limit]

    return await sync_to_async(lambda: list(queryset))()