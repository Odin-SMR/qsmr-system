from pathlib import Path

import pytest

from qsmr_system.dataset import Result


@pytest.fixture
def fm2_ok_data() -> Result:
    data = (Path(__file__).parent / "FM2_14205733121_OK.json").read_text()
    return Result.model_validate_json(data)


@pytest.fixture
def fm14_ok_data() -> Result:
    data = (Path(__file__).parent / "FM14_14994023880_OK.json").read_text()
    return Result.model_validate_json(data)


@pytest.fixture
def fm14_empty_data() -> Result:
    data = (Path(__file__).parent / "FM14_14724113814_empty.json").read_text()
    return Result.model_validate_json(data)
