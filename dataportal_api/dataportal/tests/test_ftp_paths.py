from dataportal.ingest.feature.sources import (
    isolate_names_from_ftp_entries,
    is_primary_annotations_gff,
    list_isolates_from_local,
)
from dataportal.ingest.ftp_paths import (
    DEFAULT_GFF_DIR_TEMPLATE,
    format_ftp_path,
    is_fasta_filename,
    mapping_lookup,
    parse_fasta_extensions,
    strip_fasta_extension,
)
from dataportal.ingest.strain.ftp import public_https_url


def test_format_ftp_path_matches_published_v1_gff():
    path = format_ftp_path(
        DEFAULT_GFF_DIR_TEMPLATE,
        base="/pub/databases/mett/annotations/v1_2024-04-15/",
        isolate="BU_ATCC8492",
    )
    assert (
        path
        == "/pub/databases/mett/annotations/v1_2024-04-15/BU_ATCC8492/functional_annotation/merged_gff"
    )
    assert public_https_url("ftp.ebi.ac.uk", path, "BU_ATCC8492_annotations.gff") == (
        "https://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/"
        "BU_ATCC8492/functional_annotation/merged_gff/BU_ATCC8492_annotations.gff"
    )


def test_format_ftp_path_matches_20hm_temp_gff():
    path = format_ftp_path(
        DEFAULT_GFF_DIR_TEMPLATE,
        base="/pub/databases/metagenomics/temp/mett/20hm/v1/annotations/",
        isolate="AR_VPI0990",
    )
    assert public_https_url("ftp.ebi.ac.uk", path, "AR_VPI0990_annotations.gff") == (
        "https://ftp.ebi.ac.uk/pub/databases/metagenomics/temp/mett/20hm/v1/"
        "annotations/AR_VPI0990/functional_annotation/merged_gff/"
        "AR_VPI0990_annotations.gff"
    )


def test_format_ftp_path_custom_template_omits_annotator_suffix():
    path = format_ftp_path(
        "{base}/{isolate}",
        base="/pub/databases/mett/annotations/custom",
        isolate="AR_VPI0990",
    )
    assert path == "/pub/databases/mett/annotations/custom/AR_VPI0990"


def test_fasta_extensions_include_fna():
    assert is_fasta_filename("AR_VPI0990.fna")
    assert is_fasta_filename("BU_ATCC8492VPI0062_NT5002.1.fa")
    assert not is_fasta_filename("readme.txt")
    assert parse_fasta_extensions(".fna") == (".fna",)
    assert strip_fasta_extension("AR_VPI0990.fna") == "AR_VPI0990"


def test_mapping_lookup_accepts_stem_or_extension():
    mapping = {
        "BU_ATCC8492VPI0062_NT5002.1.fa": "BU_ATCC8492",
        "AR_VPI0990": "AR_VPI0990",
    }
    assert mapping_lookup(mapping, "BU_ATCC8492VPI0062_NT5002.1.fa") == "BU_ATCC8492"
    assert mapping_lookup(mapping, "AR_VPI0990.fna") == "AR_VPI0990"


def test_public_https_url_for_20hm_assembly():
    assert public_https_url(
        "ftp.ebi.ac.uk",
        "/pub/databases/metagenomics/temp/mett/20hm/v1/assemblies/",
        "AR_VPI0990.fna",
    ) == (
        "https://ftp.ebi.ac.uk/pub/databases/metagenomics/temp/mett/20hm/v1/"
        "assemblies/AR_VPI0990.fna"
    )


def test_isolate_names_from_ftp_entries_strip_noise_and_paths():
    entries = [
        "/pub/databases/metagenomics/temp/mett/20hm/v1/annotations/AR_VPI0990",
        "EB_ATCCBAA-613",
        "multiqc",
        "pipeline_info",
        ".",
    ]
    assert isolate_names_from_ftp_entries(entries) == [
        "AR_VPI0990",
        "EB_ATCCBAA-613",
    ]


def test_is_primary_annotations_gff_skips_orig_and_descriptions():
    assert is_primary_annotations_gff("AR_VPI0990_annotations.gff")
    assert not is_primary_annotations_gff("AR_VPI0990_annotations-orig.gff")
    assert not is_primary_annotations_gff(
        "AR_VPI0990_annotations_with_descriptions.gff"
    )


def test_list_isolates_from_local(tmp_path):
    (tmp_path / "AR_VPI0990").mkdir()
    (tmp_path / "EB_ATCCBAA-613").mkdir()
    (tmp_path / "multiqc").mkdir()
    (tmp_path / "readme.txt").write_text("x")
    assert list_isolates_from_local(str(tmp_path)) == [
        "AR_VPI0990",
        "EB_ATCCBAA-613",
    ]


def test_format_ftp_path_for_local_mettannotator_root():
    path = format_ftp_path(
        DEFAULT_GFF_DIR_TEMPLATE,
        base="/Users/me/data-generators/data/generated/mettannotator",
        isolate="AR_VPI0990",
    )
    assert path.endswith("/mettannotator/AR_VPI0990/functional_annotation/merged_gff")
