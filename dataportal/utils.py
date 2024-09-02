from django.conf import settings


def construct_file_urls(strain):
    # Construct URLs using environment variables
    fasta_url = f"{settings.ASSEMBLY_FTP_PATH}{strain.fasta_file}"
    gff_url = settings.GFF_FTP_PATH.format(strain.isolate_name) + strain.gff_file

    return fasta_url, gff_url, strain.fasta_file, strain.gff_file
