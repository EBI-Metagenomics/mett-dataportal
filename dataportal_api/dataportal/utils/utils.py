from django.conf import settings
from urllib.parse import unquote

def convert_to_camel_case(text: str) -> str:
    """Convert a string to CamelCase."""
    return " ".join(word.capitalize() for word in text.split())


def construct_file_urls(strain):
    # Construct URLs using environment variables
    fasta_url = f"{settings.ASSEMBLY_FTP_PATH}/{strain.fasta_file}"
    gff_url = settings.GFF_FTP_PATH.format(strain.isolate_name) + "/" + strain.gff_file

    return fasta_url, gff_url, strain.fasta_file, strain.gff_file

def split_comma_param(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [v.strip() for v in unquote(value).split(",")]