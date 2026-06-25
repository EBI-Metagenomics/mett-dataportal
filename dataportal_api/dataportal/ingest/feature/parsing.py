def split_gff_list(value: str | None, sep: str = ",") -> list[str]:
    """Split a GFF attribute value into a list of non-empty tokens."""
    if not value:
        return []
    return [item.strip() for item in value.split(sep) if item.strip()]


def parse_extra_copy_number(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_gene_gff_annotations(attr: dict) -> dict:
    """Map GFF gene-row attributes to FeatureDocument field values."""
    return {
        "uf_keyword": split_gff_list(attr.get("uf_keyword")),
        "uf_gene_name": attr.get("uf_gene_name"),
        "uf_gene_name_synonym": attr.get("uf_gene_name_synonym"),
        "uf_prot_rec_shortname": attr.get("uf_prot_rec_shortname"),
        "uf_prot_alt_fullname": attr.get("uf_prot_alt_fullname"),
        "uf_prot_alt_shortname": attr.get("uf_prot_alt_shortname"),
        "uf_prot_alt_ecnumber": attr.get("uf_prot_alt_ecnumber"),
        "uf_chebi": split_gff_list(attr.get("uf_chebi")),
        "uf_pirsr_cofactor": attr.get("uf_pirsr_cofactor"),
        "dbcan_prot_type": attr.get("dbcan_prot_type"),
        "dbcan_prot_family": split_gff_list(attr.get("dbcan_prot_family"), sep="|"),
        "substrate_dbcan_pul": attr.get("substrate_dbcan-pul"),
        "substrate_dbcan_sub": attr.get("substrate_dbcan-sub"),
        "gecco_bgc_type": attr.get("gecco_bgc_type"),
        "nearest_mibig": attr.get("nearest_MiBIG"),
        "nearest_mibig_class": attr.get("nearest_MiBIG_class"),
        "antismash_bgc_function": attr.get("antismash_bgc_function"),
        "mge_id": attr.get("mge_id"),
        "mge_types": split_gff_list(attr.get("mge_types")),
        "defense_finder_type": attr.get("defense_finder_type"),
        "defense_finder_subtype": attr.get("defense_finder_subtype"),
        "extra_copy_number": parse_extra_copy_number(attr.get("extra_copy_number")),
        "note": attr.get("note"),
    }
