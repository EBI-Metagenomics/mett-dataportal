import pandas as pd

from dataportal.ingest.species.importer import load_species_rows, parse_enabled_flag


def test_load_species_rows_parses_false_string(tmp_path):
    csv_path = tmp_path / "species.csv"
    csv_path.write_text(
        "scientific_name,common_name,acronym,taxonomy_id,enabled\n"
        "Bacteroides uniformis,BU,BU,820,true\n"
        "Bacteroides fragilis,BF,BF,272559,false\n",
        encoding="utf-8",
    )

    df = load_species_rows(str(csv_path))
    by_acronym = dict(zip(df["acronym"], df["enabled"]))
    assert by_acronym["BU"] is True
    assert by_acronym["BF"] is False


def test_parse_enabled_flag_numeric_and_bool():
    assert parse_enabled_flag(True) is True
    assert parse_enabled_flag(False) is False
    assert parse_enabled_flag(1) is True
    assert parse_enabled_flag(0) is False
    series = pd.Series(["true", "false"])
    assert list(series.map(parse_enabled_flag)) == [True, False]
