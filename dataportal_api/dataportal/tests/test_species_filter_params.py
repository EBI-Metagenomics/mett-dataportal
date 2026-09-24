from dataportal.utils.utils import split_comma_param


def test_split_comma_param_supports_multiple_species_acronyms():
    assert split_comma_param(None) == []
    assert split_comma_param("") == []
    assert split_comma_param("BU") == ["BU"]
    assert split_comma_param("BU,PV") == ["BU", "PV"]
    assert split_comma_param("BU, PV, BF") == ["BU", "PV", "BF"]
    assert split_comma_param(["BU", "PV"]) == ["BU", "PV"]
