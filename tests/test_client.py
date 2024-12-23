import json
from unittest.mock import MagicMock, call, patch

import pytest

from app.constants import AuthorizationState
from app.telegram.client import TDLibClient


@pytest.fixture
def mock_td_client():
    """Returns a TDLibClient mock with relevant methods stubbed."""
    client = MagicMock(spec=TDLibClient)
    return client


def test_set_verbosity_level():
    with patch.object(TDLibClient, "execute") as mock_execute:
        # Instantiate the client, which triggers the first execute call
        client = TDLibClient(api_id="123", api_hash="abc")

        # Reset the mock to ignore the initial call
        mock_execute.reset_mock()

        # Now, call the method under test
        client._set_verbosity_level(3)

        # Assert that execute was called once with the expected argument
        mock_execute.assert_called_once_with({"@type": "setLogVerbosityLevel", "new_verbosity_level": 3})


def test_set_verbosity_level_multiple_calls():
    with patch.object(TDLibClient, "execute") as mock_execute:
        # Instantiate the client, triggering the first execute call
        client = TDLibClient(api_id="123", api_hash="abc")

        # Call the method under test
        client._set_verbosity_level(3)

        # Define expected calls
        expected_calls = [
            call({"@type": "setLogVerbosityLevel", "new_verbosity_level": 2}),
            call({"@type": "setLogVerbosityLevel", "new_verbosity_level": 3}),
        ]

        # Assert that execute was called twice with the expected arguments
        mock_execute.assert_has_calls(expected_calls)

        # Additionally, assert that execute was called exactly twice
        assert mock_execute.call_count == 2


def test_is_authorized(mock_td_client):
    mock_td_client.is_authorized.return_value = True
    assert mock_td_client.is_authorized() is True


def test_send(mock_td_client):
    data = {"@type": "testSend", "data": "payload"}
    mock_td_client.send(data)
    mock_td_client.send.assert_called_once_with(data)


def test_receive(mock_td_client):
    mock_td_client.receive.return_value = {"@type": "someUpdate"}
    client = TDLibClient(api_id="123", api_hash="abc")
    with patch.object(client, "receive", return_value={"@type": "someUpdate"}):
        result = client.receive(timeout=0.1)
        assert result["@type"] == "someUpdate"


def test_execute():
    with patch("app.telegram.functional.execute") as mock_execute:
        mock_execute.return_value = json.dumps({"@type": "someType"}).encode("utf-8")
        client = TDLibClient(api_id="123", api_hash="abc")
        result = client.execute({"@type": "testQuery"})
        assert result["@type"] == "someType"


def test_login_step_changes_state():
    # Initialize the TDLibClient instance
    client = TDLibClient(api_id="123", api_hash="abc")

    with patch.object(client, "send") as mock_send, patch.object(client, "process_all_updates") as mock_updates:
        # Define a side effect function that updates the internal state
        def mock_process_all_updates():
            client._authorization_state = AuthorizationState.READY
            return AuthorizationState.READY

        # Assign the side effect to the mocked method
        mock_updates.side_effect = mock_process_all_updates

        # Call the method under test
        state = client.login_step()

        # Assertions
        mock_send.assert_called_once_with({"@type": "getAuthorizationState"})
        assert state == AuthorizationState.READY


def test_login_step_no_state_change():
    # Initialize the TDLibClient instance
    client = TDLibClient(api_id="123", api_hash="abc")

    with patch.object(client, "send") as mock_send, patch.object(client, "process_all_updates") as mock_updates:
        # Define a side effect function that does not change the internal state
        def mock_process_all_updates():
            return AuthorizationState.NONE

        # Assign the side effect to the mocked method
        mock_updates.side_effect = mock_process_all_updates

        # Call the method under test
        state = client.login_step()

        # Assertions
        mock_send.assert_called_once_with({"@type": "getAuthorizationState"})
        assert state == AuthorizationState.NONE
