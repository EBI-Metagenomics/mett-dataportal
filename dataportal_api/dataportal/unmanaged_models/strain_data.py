from django.db import models

from dataportal import settings
from dataportal.utils.constants import (
    STRAIN_FIELD_ISOLATE_NAME,
    STRAIN_FIELD_ASSEMBLY_NAME,
    STRAIN_FIELD_ASSEMBLY_ACCESSION,
    STRAIN_FIELD_FASTA_FILE,
    STRAIN_FIELD_GFF_FILE,
    STRAIN_FIELD_TYPE_STRAIN,
    ES_FIELD_SPECIES_ACRONYM,
    ES_FIELD_SPECIES_SCIENTIFIC_NAME,
    STRAIN_FIELD_FASTA_URL,
    STRAIN_FIELD_GFF_URL,
    STRAIN_FIELD_CONTIGS,
)


class StrainData(models.Model):
    locals()[ES_FIELD_SPECIES_SCIENTIFIC_NAME] = models.CharField(max_length=500)
    locals()[ES_FIELD_SPECIES_ACRONYM] = models.CharField(max_length=50)
    locals()[STRAIN_FIELD_ISOLATE_NAME] = models.CharField(max_length=255)
    locals()[STRAIN_FIELD_ASSEMBLY_NAME] = models.CharField(max_length=255)
    locals()[STRAIN_FIELD_ASSEMBLY_ACCESSION] = models.CharField(
        max_length=100, null=True
    )
    locals()[STRAIN_FIELD_FASTA_FILE] = models.CharField(max_length=255, null=True)
    locals()[STRAIN_FIELD_GFF_FILE] = models.CharField(max_length=255, null=True)
    locals()[STRAIN_FIELD_TYPE_STRAIN] = models.BooleanField(default=False)

    locals()[STRAIN_FIELD_FASTA_URL] = models.URLField(null=True)
    locals()[STRAIN_FIELD_GFF_URL] = models.URLField(null=True)

    locals()[STRAIN_FIELD_CONTIGS] = models.JSONField(null=True, default=list)

    class Meta:
        managed = False


def strain_from_hit(hit) -> StrainData:
    source = hit.to_dict()
    return StrainData(
        isolate_name=source.get(STRAIN_FIELD_ISOLATE_NAME),
        species_scientific_name=source.get(ES_FIELD_SPECIES_SCIENTIFIC_NAME),
        species_acronym=source.get(ES_FIELD_SPECIES_ACRONYM),
        assembly_name=source.get(STRAIN_FIELD_ASSEMBLY_NAME),
        assembly_accession=source.get(STRAIN_FIELD_ASSEMBLY_ACCESSION),
        fasta_file=source.get(STRAIN_FIELD_FASTA_FILE),
        gff_file=source.get(STRAIN_FIELD_GFF_FILE),
        type_strain=source.get(STRAIN_FIELD_TYPE_STRAIN, False),
        fasta_url=(
            f"{settings.ASSEMBLY_FTP_PATH}/{source.get(STRAIN_FIELD_FASTA_FILE)}"
            if source.get(STRAIN_FIELD_FASTA_FILE)
            else None
        ),
        gff_url=(
            f"{settings.GFF_FTP_PATH.format(source.get(STRAIN_FIELD_ISOLATE_NAME))}/{source.get(STRAIN_FIELD_GFF_FILE)}"
            if source.get(STRAIN_FIELD_GFF_FILE)
            and source.get(STRAIN_FIELD_ISOLATE_NAME)
            else None
        ),
        contigs=source.get(STRAIN_FIELD_CONTIGS, []),
    )
