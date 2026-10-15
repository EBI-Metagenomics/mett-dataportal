"""Checks for the search steps that do not need a database."""

from types import SimpleNamespace
from unittest.mock import Mock

from pyhmmer.plan7 import Domain, Hit

from pyhmmer_search.execution.hits import build_hits
from pyhmmer_search.execution.schemas import (
    PipelineParameters,
    QuerySequence,
    SearchScope,
)


def test_query_keeps_the_fasta_name_and_joins_sequence_lines():
    query = QuerySequence.parse_fasta(">BU_00001 extra\nMSEI\nDHVG")
    assert query.name == "BU_00001 extra"
    assert query.sequence == "MSEIDHVG"


def test_pipeline_parameters_drop_unset_thresholds():
    parameters = PipelineParameters(E=1.0, incE=0.01, popen=0.02, pextend=None)
    assert parameters.pipeline_kwargs() == {"E": 1.0, "incE": 0.01}
    assert parameters.builder_kwargs() == {"popen": 0.02}


def test_old_database_alias_becomes_a_species_filter():
    job = SimpleNamespace(database="bu_all", species=[], type_only=False, isolate="")
    scope = SearchScope.from_job(job)
    assert scope.species == ["BU"]
    assert scope.type_only is False
    assert scope.isolate == ""


def test_explicit_species_overrides_an_old_database_alias():
    job = SimpleNamespace(database="bu_all", species=["PV"], type_only=True, isolate="")
    scope = SearchScope.from_job(job)
    assert scope.species == ["PV"]
    assert scope.type_only is True


def test_phmmer_hit_expands_to_one_row_per_locus_tag():
    hit = Mock(spec=Hit)
    hit.name = b"BU_ATCC8492_00001"
    hit.description = b"hypothetical protein [Bacteroides]"
    hit.evalue = 1e-25
    hit.score = 95.5
    hit.included = True
    hit.bias = 0.1
    hit.domains = []
    hit.envelope_from = None
    hit.envelope_to = None
    hit.c_evalue = None

    target = SimpleNamespace(sequence="MSEIDHVG")
    membership = {
        "BU_ATCC8492_00001": {
            "locus_tags": ["BU_ATCC8492_00001", "PV_ATCC8482_00456"],
            "product": "hypothetical protein",
        }
    }
    hits = build_hits(
        [hit],
        query=QuerySequence(name="query", sequence="MSEIDHVG"),
        target_sequences={"BU_ATCC8492_00001": target},
        threshold="evalue",
        inc_e=0.01,
        inc_t=25.0,
        membership=membership,
    )

    assert [item.target for item in hits] == [
        "BU_ATCC8492_00001",
        "PV_ATCC8482_00456",
    ]
    assert hits[0].seq_id == "BU_ATCC8492_00001"
    assert hits[0].description == "hypothetical protein"
    assert hits[0].is_significant is True
    assert hits[0].domains[0].is_significant is True
    assert hits[0].num_hits == 1
    assert hits[0].num_significant == 1


def test_domain_significance_uses_the_reporting_threshold():
    hit = SimpleNamespace(
        name=b"gene",
        description=b"product=kinase lt=gene",
        evalue=1e-3,
        score=10.0,
        bias=None,
    )
    strong = Mock(spec=Domain)
    strong.env_from = 1
    strong.env_to = 10
    strong.score = 40.0
    strong.i_evalue = 1e-8
    strong.c_evalue = None
    strong.bias = None
    strong.strand = None
    strong.alignment = None
    weak = Mock(spec=Domain)
    weak.env_from = 20
    weak.env_to = 30
    weak.score = 10.0
    weak.i_evalue = 0.2
    weak.c_evalue = None
    weak.bias = None
    weak.strand = None
    weak.alignment = None
    hit.domains = [strong, weak]

    hits = build_hits(
        [hit],
        query=QuerySequence(name="query", sequence="AAAA"),
        target_sequences={},
        threshold="evalue",
        inc_e=0.01,
        inc_t=25.0,
        membership=None,
    )

    assert hits[0].description == "kinase"
    assert hits[0].num_significant == 1
    assert [domain.is_significant for domain in hits[0].domains] == [True, False]
    assert hits[0].target == "gene"
