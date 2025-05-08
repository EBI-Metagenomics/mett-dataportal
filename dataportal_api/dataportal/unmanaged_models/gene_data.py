from django.db import models
from dataportal.utils.constants import (
    ES_FIELD_AMR,
    ES_FIELD_AMR_INFO,
    ES_FIELD_LOCUS_TAG,
    ES_FIELD_GENE_NAME,
    ES_FIELD_ALIAS,
    ES_FIELD_PRODUCT,
    GENE_FIELD_START_POS,
    GENE_FIELD_END_POS,
    FIELD_SEQ_ID,
    ES_FIELD_ISOLATE_NAME,
    ES_FIELD_UNIPROT_ID,
    GENE_ESSENTIALITY,
    ES_FIELD_COG_FUNCATS,
    ES_FIELD_COG_ID,
    ES_FIELD_KEGG,
    ES_FIELD_PFAM,
    ES_FIELD_INTERPRO,
    GENE_FIELD_EC_NUMBER,
    GENE_FIELD_DBXREF,
    UNKNOWN_ESSENTIALITY, GENE_FIELD_START,
    GENE_FIELD_END,
    ES_FIELD_EGGNOG,
    ES_FIELD_SPECIES_ACRONYM,
    ES_FIELD_SPECIES_SCIENTIFIC_NAME,
)


class GeneData(models.Model):
    locals()[ES_FIELD_LOCUS_TAG] = models.CharField(max_length=100, null=True)
    locals()[ES_FIELD_GENE_NAME] = models.CharField(max_length=255, null=True)
    locals()[ES_FIELD_ALIAS] = models.JSONField(null=True, default=list)
    locals()[ES_FIELD_PRODUCT] = models.TextField(null=True)
    locals()[GENE_FIELD_START_POS] = models.IntegerField(null=True)
    locals()[GENE_FIELD_END_POS] = models.IntegerField(null=True)
    locals()[FIELD_SEQ_ID] = models.CharField(max_length=100, null=True)
    locals()[ES_FIELD_ISOLATE_NAME] = models.CharField(max_length=100, null=True)
    locals()[ES_FIELD_SPECIES_SCIENTIFIC_NAME] = models.CharField(max_length=100, null=True)
    locals()[ES_FIELD_SPECIES_ACRONYM] = models.CharField(max_length=100, null=True)
    locals()[ES_FIELD_UNIPROT_ID] = models.CharField(max_length=100, null=True)
    locals()[GENE_ESSENTIALITY] = models.CharField(max_length=100, null=True, default=UNKNOWN_ESSENTIALITY)
    locals()[ES_FIELD_COG_FUNCATS] = models.JSONField(null=True, default=list)
    locals()[ES_FIELD_COG_ID] = models.CharField(max_length=100, null=True)
    locals()[ES_FIELD_KEGG] = models.JSONField(null=True, default=list)
    locals()[ES_FIELD_PFAM] = models.JSONField(null=True, default=list)
    locals()[ES_FIELD_INTERPRO] = models.JSONField(null=True, default=list)
    locals()[GENE_FIELD_EC_NUMBER] = models.CharField(max_length=100, null=True)
    locals()[GENE_FIELD_DBXREF] = models.JSONField(null=True, default=list)
    locals()[ES_FIELD_EGGNOG] = models.CharField(max_length=255, null=True)
    locals()[ES_FIELD_AMR] = models.JSONField(null=True, default=list)
    locals()[ES_FIELD_AMR_INFO] = models.BooleanField(null=True, default=False)

    class Meta:
        managed = False


def gene_from_hit(hit) -> GeneData:
    source = hit.to_dict()

    return GeneData(
        locus_tag=source.get(ES_FIELD_LOCUS_TAG),
        gene_name=source.get(ES_FIELD_GENE_NAME),
        alias=source.get(ES_FIELD_ALIAS, []),
        product=source.get(ES_FIELD_PRODUCT),
        start_position=source.get(GENE_FIELD_START, source.get(GENE_FIELD_START_POS)),
        end_position=source.get(GENE_FIELD_END, source.get(GENE_FIELD_END_POS)),
        seq_id=source.get(FIELD_SEQ_ID),
        isolate_name=source.get(ES_FIELD_ISOLATE_NAME),
        species_scientific_name=source.get(ES_FIELD_SPECIES_SCIENTIFIC_NAME),
        species_acronym=source.get(ES_FIELD_SPECIES_ACRONYM),
        uniprot_id=source.get(ES_FIELD_UNIPROT_ID),
        essentiality=source.get(GENE_ESSENTIALITY, UNKNOWN_ESSENTIALITY),
        cog_funcats=source.get(ES_FIELD_COG_FUNCATS, []),
        cog_id=source.get(ES_FIELD_COG_ID),
        kegg=source.get(ES_FIELD_KEGG, []),
        pfam=source.get(ES_FIELD_PFAM, []),
        interpro=source.get(ES_FIELD_INTERPRO, []),
        ec_number=source.get(GENE_FIELD_EC_NUMBER),
        dbxref=source.get(GENE_FIELD_DBXREF, []),
        eggnog=source.get(ES_FIELD_EGGNOG),
        amr=source.get(ES_FIELD_AMR, []),
        has_amr_info=source.get(ES_FIELD_AMR_INFO),
    )
