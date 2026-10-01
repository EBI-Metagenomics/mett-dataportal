from dataportal.utils.utils import split_comma_values


def test_split_comma_values_treats_a_joined_list_as_separate_names():
    assert split_comma_values(["BU_ATCC8492,PV_ATCC8482"]) == [
        "BU_ATCC8492",
        "PV_ATCC8482",
    ]


def test_split_comma_values_keeps_repeated_params():
    assert split_comma_values(["BU_ATCC8492", "PV_ATCC8482"]) == [
        "BU_ATCC8492",
        "PV_ATCC8482",
    ]
