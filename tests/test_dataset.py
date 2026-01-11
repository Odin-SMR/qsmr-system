from qsmr_system.dataset import Result, l2_dataframe, l2i_dataframe


def test_l2_fm2_dataframe(fm2_ok_data: Result) -> None:
    df = l2_dataframe(fm2_ok_data.L2)
    assert len(df) == 129


def test_l2i_fm2_dataframe(fm2_ok_data: Result) -> None:
    df = l2i_dataframe(fm2_ok_data.L2I, 0)
    assert len(df.iloc[0]["bline_offset"]) == 4


def test_l2_fm14_dataframe(fm14_ok_data: Result) -> None:
    df = l2_dataframe(fm14_ok_data.L2)
    assert len(df) == 20


def test_l2i_fm14_dataframe(fm14_ok_data: Result) -> None:
    df = l2i_dataframe(fm14_ok_data.L2I, 0)
    assert len(df.iloc[0]["bline_offset"]) == 4
