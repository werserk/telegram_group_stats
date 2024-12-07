import json
from unittest.mock import patch

from app.telegram.client import TDLibClient


def test_execute_returns_json():
    with patch("app.telegram.functional.execute") as mock_execute:
        mock_execute.return_value = json.dumps({"@type": "someType"}).encode("utf-8")
        result = TDLibClient.execute({"@type": "testQuery"})
        assert result["@type"] == "someType"
