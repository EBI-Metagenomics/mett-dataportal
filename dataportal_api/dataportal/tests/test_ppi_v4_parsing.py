"""PPI v4 file parsing and the document payload checked against the source rows."""

import os
import tempfile

from dataportal.ingest.ppi.parsing import iter_ppi_rows
from dataportal.ingest.ppi.ppi_csv import PPICSVFlow
from dataportal.services.interactions.ppi_service import PPIService


V4_HEADER = (
    "GeneA\tGeneB\tEdgeID\tRank\tConsensusScore\tRawConsensusScore\tQ_PPI\t"
    "Q_ChemicalGenetic\tQ_Coexpression\tQ_Operons\tQ_Metabolic\t"
    "n_evidence_types\tn_networks_total\tn_PPI\tn_ChemicalGenetic\t"
    "n_Coexpression\tn_Operons\tn_Metabolic\tScore_PPI-DsScore"
)

V4_ROWS = [
    (
        "BU_ATCC8492_02346\tBU_ATCC8492_02347\t6196593\t1\t"
        "0.99991936300950024\t0.99991936300950024\t0.99898150906671435\t"
        "0.21158603417127972\t0.0054848598837337103\t0.86516772861615043\t"
        "0.25111076952689726\t5\t16\t9\t1\t1\t4\t1\t0.71142"
    ),
    (
        "BU_ATCC8492_01640\tBU_ATCC8492_01642\t4883044\t2\t"
        "0.99991607557925577\t0.99991607557925577\t0.99898150906671435\t"
        "0.79704194939062656\t0.0063546307900920074\t0.59140458458178924\t"
        "0\t4\t9\t5\t1\t1\t2\t0\t"
    ),
]

OLD_HEADER = (
    "GeneA\tGeneB\tRank\tWeight\tScore\tEdgeID\tConsensusScore\tAvgRank\tn_sources\t"
    "Rank_Coexp\tScore_Coexp\tRank_PPI-DsScore\tScore_PPI-DsScore"
)
OLD_ROWS = [
    (
        "BU_ATCC8492_03874\tBU_ATCC8492_03875\t1\t0.702061\t0.702061\t7385256\t1\t"
        "8158.11\t13\t\t\t1591\t0.71142"
    ),
    (
        "BU_ATCC8492_01341\tBU_ATCC8492_01366\t2\t0.71893\t0.71893\t4192142\t0.96086\t"
        "8918.11\t11\t\t\t125\t0.868562"
    ),
]

DEPRECATED_FIELDS = (
    "ds_score",
    "weight_coexp",
    "n_sources",
    "interaction_weight",
    "consensus_avg_rank",
    "string_score",
    "operon_score",
)


def _write_tsv(directory: str, name: str, header: str, rows: list[str]) -> None:
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(header + "\n")
        handle.write("\n".join(rows) + "\n")


def _parse(directory: str) -> list[dict]:
    return list(iter_ppi_rows(directory, "*.tsv"))


def test_v4_rows_keep_source_scores_and_drop_source_specific_columns():
    with tempfile.TemporaryDirectory() as directory:
        _write_tsv(directory, "bu_ppi_v4.tsv", V4_HEADER, V4_ROWS)
        rows = _parse(directory)

    assert len(rows) == 2
    first, second = rows

    assert first["protein_a_locus_tag"] == "BU_ATCC8492_02346"
    assert first["protein_b_locus_tag"] == "BU_ATCC8492_02347"
    assert first["edge_id"] == "6196593"
    assert first["consensus_rank"] == 1
    assert first["consensus_score"] == float("0.99991936300950024")
    assert first["raw_consensus_score"] == float("0.99991936300950024")
    assert first["q_ppi"] == float("0.99898150906671435")
    assert first["q_chemical_genetic"] == float("0.21158603417127972")
    assert first["q_coexpression"] == float("0.0054848598837337103")
    assert first["q_operons"] == float("0.86516772861615043")
    assert first["q_metabolic"] == float("0.25111076952689726")
    assert first["n_evidence_types"] == 5
    assert first["n_networks_total"] == 16
    assert first["n_ppi"] == 9
    assert first["n_chemical_genetic"] == 1
    assert first["n_coexpression"] == 1
    assert first["n_operons"] == 4
    assert first["n_metabolic"] == 1
    assert first["species_acronym"] == "BU"

    assert second["q_metabolic"] == 0.0
    assert second["n_metabolic"] == 0
    assert second["n_evidence_types"] == 4
    assert second["n_networks_total"] == 9
    assert second["consensus_score"] == float("0.99991607557925577")

    for row in rows:
        for field in DEPRECATED_FIELDS:
            assert field not in row


def test_legacy_consensus_keeps_consensus_score_not_the_old_weight():
    with tempfile.TemporaryDirectory() as directory:
        _write_tsv(directory, "bu_ppi_v1.tsv", OLD_HEADER, OLD_ROWS)
        rows = _parse(directory)

    assert rows[0]["consensus_score"] == 1.0
    assert rows[0]["consensus_score"] != float("0.702061")
    assert rows[0]["n_networks_total"] == 13
    assert rows[0]["edge_id"] == "7385256"
    assert rows[0].get("q_ppi") is None

    assert rows[1]["consensus_score"] == float("0.96086")
    assert rows[1]["n_networks_total"] == 11

    for row in rows:
        for field in DEPRECATED_FIELDS:
            assert field not in row


def test_indexed_document_matches_v4_source_scores_and_category_flags():
    with tempfile.TemporaryDirectory() as directory:
        _write_tsv(directory, "bu_ppi_v4.tsv", V4_HEADER, V4_ROWS)
        parsed = _parse(directory)

    repo = type("Repo", (), {"concrete_index": "ppi_v4_test"})()
    flow = PPICSVFlow(repo=repo, species_map={})
    documents = [flow._row_to_action(row)["_source"] for row in parsed]
    first, second = documents

    assert first["consensus_score"] == float("0.99991936300950024")
    assert first["q_operons"] == float("0.86516772861615043")
    assert first["n_networks_total"] == 16
    assert first["n_ppi"] == 9
    assert first["has_ppi"] is True
    assert first["has_metabolic"] is True
    assert first["evidence_count"] == 5
    assert first["pair_id"] == "BU:BU_ATCC8492_02346__BU_ATCC8492_02347"

    assert second["q_metabolic"] == 0.0
    assert second["n_metabolic"] == 0
    assert second["has_metabolic"] is False
    assert second["has_ppi"] is True
    assert second["evidence_count"] == 4

    for document in documents:
        for field in DEPRECATED_FIELDS:
            assert field not in document


def test_score_type_aliases_map_to_v4_fields():
    service = PPIService()
    assert service._validate_and_normalize_score_field("consensus_score") == "consensus_score"
    assert service._validate_and_normalize_score_field("ppi") == "q_ppi"
    assert service._validate_and_normalize_score_field("operons") == "q_operons"
    assert service._validate_and_normalize_score_field("chemical-genetic") == "q_chemical_genetic"
    try:
        service._validate_and_normalize_score_field("ds_score")
    except Exception as exc:
        assert "ds_score" in str(exc)
    else:
        raise AssertionError("ds_score should no longer be a valid score type")
