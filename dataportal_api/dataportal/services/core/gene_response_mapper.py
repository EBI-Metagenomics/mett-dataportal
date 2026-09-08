"""Map flat feature_index documents to grouped GeneResponseSchema objects."""

from __future__ import annotations

from typing import Any, Dict, Optional, Type, TypeVar

from dataportal.schema.core.gene_schemas import (
    AMRSchema,
    DBXRefSchema,
    GeneBgcAnnotationSchema,
    GeneDbcanAnnotationSchema,
    GeneDefenseAnnotationSchema,
    GeneMetadataSchema,
    GeneMobilomeAnnotationSchema,
    GeneResponseSchema,
    GeneUnifireAnnotationSchema,
)

T = TypeVar("T")


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, list) and not value:
        return False
    return True


def _build_group(model_cls: Type[T], **fields: Any) -> Optional[T]:
    if not any(_has_value(value) for value in fields.values()):
        return None
    return model_cls(**fields)


def _build_metadata(hit_dict: Dict[str, Any]) -> Optional[GeneMetadataSchema]:
    note = hit_dict.get("note")
    extra_copy_number = hit_dict.get("extra_copy_number")
    if not _has_value(note) and not (extra_copy_number is not None and extra_copy_number != 0):
        return None
    return GeneMetadataSchema(extra_copy_number=extra_copy_number, note=note)


def hit_dict_to_gene_response(hit_dict: Dict[str, Any]) -> GeneResponseSchema:
    """Convert a flat Elasticsearch gene document into a grouped API response."""
    dbxref_raw = hit_dict.get("dbxref") or []
    dbxref = [DBXRefSchema(**item) for item in dbxref_raw if isinstance(item, dict)]

    amr_raw = hit_dict.get("amr") or []
    amr = [AMRSchema(**item) for item in amr_raw if isinstance(item, dict)]

    unifire = _build_group(
        GeneUnifireAnnotationSchema,
        gene_name=hit_dict.get("uf_gene_name"),
        gene_name_synonym=hit_dict.get("uf_gene_name_synonym"),
        keywords=hit_dict.get("uf_keyword", []),
        ontology_terms=hit_dict.get("uf_ontology_terms", []),
        protein_fullname=hit_dict.get("uf_prot_rec_fullname"),
        protein_shortname=hit_dict.get("uf_prot_rec_shortname"),
        protein_ec_number=hit_dict.get("uf_prot_rec_ecnumber"),
        alt_protein_fullname=hit_dict.get("uf_prot_alt_fullname"),
        alt_protein_shortname=hit_dict.get("uf_prot_alt_shortname"),
        alt_ec_number=hit_dict.get("uf_prot_alt_ecnumber"),
        chebi=hit_dict.get("uf_chebi", []),
        pirsr_cofactor=hit_dict.get("uf_pirsr_cofactor"),
    )

    dbcan = _build_group(
        GeneDbcanAnnotationSchema,
        prot_type=hit_dict.get("dbcan_prot_type"),
        prot_family=hit_dict.get("dbcan_prot_family", []),
        substrate_pul=hit_dict.get("substrate_dbcan_pul"),
        substrate_sub=hit_dict.get("substrate_dbcan_sub"),
    )

    bgc = _build_group(
        GeneBgcAnnotationSchema,
        gecco_bgc_type=hit_dict.get("gecco_bgc_type"),
        nearest_mibig=hit_dict.get("nearest_mibig"),
        nearest_mibig_class=hit_dict.get("nearest_mibig_class"),
        antismash_bgc_function=hit_dict.get("antismash_bgc_function"),
    )

    mobilome = _build_group(
        GeneMobilomeAnnotationSchema,
        mge_id=hit_dict.get("mge_id"),
        mge_types=hit_dict.get("mge_types", []),
    )

    defense = _build_group(
        GeneDefenseAnnotationSchema,
        finder_type=hit_dict.get("defense_finder_type"),
        finder_subtype=hit_dict.get("defense_finder_subtype"),
    )

    metadata = _build_metadata(hit_dict)

    return GeneResponseSchema(
        locus_tag=hit_dict.get("locus_tag"),
        gene_name=hit_dict.get("gene_name"),
        alias=hit_dict.get("alias", []),
        product=hit_dict.get("product"),
        product_source=hit_dict.get("product_source"),
        start_position=hit_dict.get("start", hit_dict.get("start_position")),
        end_position=hit_dict.get("end", hit_dict.get("end_position")),
        seq_id=hit_dict.get("seq_id"),
        isolate_name=hit_dict.get("isolate_name"),
        species_scientific_name=hit_dict.get("species_scientific_name"),
        species_acronym=hit_dict.get("species_acronym"),
        uniprot_id=hit_dict.get("uniprot_id"),
        essentiality=hit_dict.get("essentiality", "Unknown"),
        cog_funcats=hit_dict.get("cog_funcats", []),
        cog_id=hit_dict.get("cog_id", []),
        kegg=hit_dict.get("kegg", []),
        pfam=hit_dict.get("pfam", []),
        interpro=hit_dict.get("interpro", []),
        ec_number=hit_dict.get("ec_number"),
        dbxref=dbxref,
        eggnog=hit_dict.get("eggnog"),
        inference=hit_dict.get("inference"),
        ontology_terms=hit_dict.get("ontology_terms", []),
        uf_ontology_terms=hit_dict.get("uf_ontology_terms", []),
        uf_prot_rec_fullname=hit_dict.get("uf_prot_rec_fullname"),
        uf_keyword=hit_dict.get("uf_keyword", []),
        uf_gene_name=hit_dict.get("uf_gene_name"),
        amr=amr,
        has_amr_info=hit_dict.get("has_amr_info", False),
        has_proteomics=hit_dict.get("has_proteomics", False),
        has_fitness=hit_dict.get("has_fitness", False),
        has_mutant_growth=hit_dict.get("has_mutant_growth", False),
        has_reactions=hit_dict.get("has_reactions", False),
        feature_type=hit_dict.get("feature_type", "gene"),
        ig_locus_tag_a=hit_dict.get("ig_locus_tag_a"),
        ig_locus_tag_b=hit_dict.get("ig_locus_tag_b"),
        flanking_locus_tags=hit_dict.get("flanking_locus_tags"),
        unifire=unifire,
        dbcan=dbcan,
        bgc=bgc,
        mobilome=mobilome,
        defense=defense,
        metadata=metadata,
    )
