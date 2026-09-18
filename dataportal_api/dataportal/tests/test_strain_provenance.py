from dataportal.elasticsearch.history import (
    ReleaseAlias,
    alias_names,
    aliases_from_releases,
    dedupe_appearances,
    map_index_name_to_release,
    parse_release_from_index_name,
    version_sort_key,
)
from dataportal.ingest.strain.provenance import (
    apply_annotation,
    build_annotation_payload,
    isolate_allowed,
    parse_isolate_allowlist,
)
from dataportal.models.strains import StrainAnnotation, StrainDocument
from dataportal.schema.core.genome_schemas import StrainAnnotationSchema
from dataportal.schema.core.release_history_schemas import GeneReleaseAppearanceSchema
from dataportal.services.core.genome_service import GenomeService, _annotation_schema
from dataportal.ingest.strain.ftp import public_https_url


def test_strain_document_mapping_includes_annotation():
    mapping = StrainDocument._index.to_dict()
    properties = mapping["mappings"]["properties"]
    assert "annotation" in properties
    annotation_props = properties["annotation"]["properties"]
    assert set(annotation_props) >= {
        "pipeline",
        "pipeline_version",
        "processing_reference",
        "processing_document_url",
    }


def test_strain_document_mapping_includes_file_urls():
    properties = StrainDocument._index.to_dict()["mappings"]["properties"]
    assert "fasta_url" in properties
    assert "gff_url" in properties


def test_public_https_url_joins_ftp_host_and_paths():
    assert (
        public_https_url(
            "ftp.ebi.ac.uk",
            "/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/",
            "BU_ATCC8492.fa",
        )
        == "https://ftp.ebi.ac.uk/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/BU_ATCC8492.fa"
    )


def test_genome_schema_uses_stored_fasta_and_gff_urls():
    class Hit:
        def to_dict(self):
            return {
                "isolate_name": "BU_ATCC8492",
                "fasta_file": "x.fa",
                "gff_file": "x.gff",
                "fasta_url": "https://example.org/custom/x.fa",
                "gff_url": "https://example.org/other/x.gff",
                "type_strain": True,
                "contigs": [],
            }

    genome = GenomeService()._convert_hit_to_genome_schema(Hit())
    assert genome.fasta_url == "https://example.org/custom/x.fa"
    assert genome.gff_url == "https://example.org/other/x.gff"


def test_strain_annotation_inner_doc_round_trip():
    block = StrainAnnotation(
        pipeline="mettannotator",
        pipeline_version="2.0",
        processing_reference="processing-v2.0",
        processing_document_url="https://example.org/processing-v2.0.md",
    )
    dumped = block.to_dict()
    assert dumped["pipeline"] == "mettannotator"
    schema = _annotation_schema(dumped)
    assert isinstance(schema, StrainAnnotationSchema)
    assert schema.pipeline_version == "2.0"


def test_annotation_schema_empty_is_none():
    assert _annotation_schema({}) is None
    assert _annotation_schema(None) is None


def test_build_annotation_payload_omitted_flags_leave_none():
    assert build_annotation_payload() is None
    assert build_annotation_payload(pipeline="", pipeline_version="  ") is None


def test_build_annotation_payload_partial_flags():
    payload = build_annotation_payload(pipeline="mettannotator", pipeline_version="1.4")
    assert payload["pipeline"] == "mettannotator"
    assert payload["pipeline_version"] == "1.4"
    assert payload["processing_reference"] is None


def test_apply_annotation_does_not_clear_when_payload_missing():
    class Doc:
        annotation = {"pipeline": "keep-me"}

    doc = Doc()
    apply_annotation(doc, None)
    assert doc.annotation == {"pipeline": "keep-me"}
    apply_annotation(doc, {"pipeline": "mettannotator", "pipeline_version": "2.0"})
    assert doc.annotation["pipeline"] == "mettannotator"


def test_parse_isolate_allowlist_comma_and_file(tmp_path):
    assert parse_isolate_allowlist() is None
    assert parse_isolate_allowlist(isolates="BU_ATCC8492, PV_ATCC8482") == {
        "BU_ATCC8492",
        "PV_ATCC8482",
    }
    path = tmp_path / "isolates.txt"
    path.write_text("# comment\nATCC8482\nStrain X,Strain Y\n")
    assert parse_isolate_allowlist(isolates_file=str(path)) == {
        "ATCC8482",
        "Strain X",
        "Strain Y",
    }


def test_isolate_allowed_filters_mixed_pipeline_batch():
    allow = {"ATCC8482", "PV_ATCC8482"}
    assert isolate_allowed("PV_ATCC8482", allow)
    assert isolate_allowed("other", allow, "ATCC8482")
    assert not isolate_allowed("ATCC8492", allow)
    assert isolate_allowed("anyone", None)


def test_aliases_from_releases_skips_current_alias():
    class Indexes:
        def __init__(self, items):
            self._items = items

        def all(self):
            return self._items

    class IndexRow:
        def __init__(self, family, alias, physical_index):
            self.family = family
            self.alias = alias
            self.physical_index = physical_index

    class Release:
        def __init__(self, version, status, indexes):
            self.version = version
            self.status = status
            self.indexes = Indexes(indexes)

    releases = [
        Release(
            "v1",
            "archived",
            [IndexRow("strains", "mett-v1-strains", "mett-v1-g001-strains")],
        ),
        Release(
            "v3",
            "current",
            [IndexRow("strains", "mett-v3-strains", "mett-v3-g001-strains")],
        ),
        Release(
            "v2",
            "ready",
            [IndexRow("strains", "mett-current-strains", "mett-v2-g001-strains")],
        ),
    ]
    rows = aliases_from_releases(releases, "strains")
    names = alias_names(rows)
    assert names == ["mett-v1-strains", "mett-v3-strains"]
    assert "mett-current-strains" not in names
    assert [row.version for row in rows] == ["v1", "v3"]
    assert rows[1].is_current is True


def test_map_physical_index_to_release():
    rows = [
        ReleaseAlias(
            "v1", "archived", "mett-v1-strains", "mett-v1-g001-strains", False
        ),
        ReleaseAlias("v3", "current", "mett-v3-strains", "mett-v3-g002-strains", True),
    ]
    mapped = map_index_name_to_release("mett-v1-g001-strains", rows, "strains")
    assert mapped is not None
    assert mapped.version == "v1"
    parsed = parse_release_from_index_name("mett-v3-g002-strains", "strains")
    assert parsed == ("v3", "strains")
    assert parse_release_from_index_name("mett-current-strains") is None


def test_dedupe_appearances_drops_current_duplicate():
    appearances = [
        {"version": "v3", "status": "current", "is_current": True},
        {"version": "v3", "status": "current", "is_current": True},
        {"version": "v1", "status": "archived", "is_current": False},
    ]
    unique = dedupe_appearances(appearances)
    assert [row["version"] for row in unique] == ["v1", "v3"]
    assert version_sort_key("v10") > version_sort_key("v2")


def test_gene_release_appearance_carries_strain_annotation():
    row = GeneReleaseAppearanceSchema(
        version="v1",
        status="current",
        is_current=True,
        isolate_name="BU_ATCC8492",
        annotation=StrainAnnotationSchema(
            pipeline="mettannotator",
            pipeline_version="1.0",
            processing_reference="annotation_release_v1.0",
            processing_document_url="https://example.org/doc",
        ),
    )
    dumped = row.model_dump()
    assert dumped["annotation"]["pipeline"] == "mettannotator"
    assert "product" not in dumped
