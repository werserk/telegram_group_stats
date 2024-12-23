import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.telegram.client import TDLibClient  # noqa: E402


@pytest.fixture
def mock_td_client() -> TDLibClient:
    """Returns a TDLibClient mock with relevant methods stubbed."""
    client = MagicMock(spec=TDLibClient)
    return client
