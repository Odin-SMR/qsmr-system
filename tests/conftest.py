from pathlib import Path

import pytest

from qsmr_system.dataset import Result


@pytest.fixture
def sample_data() -> Result:
    data = (Path(__file__).parent / "debug.json").read_text()
    return Result.model_validate_json(data)
