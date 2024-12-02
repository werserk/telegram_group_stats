import json
import sys
from ctypes import CDLL, c_int, c_char_p


class TDLibClient:
    def __init__(self, tdlib_path: str, api_id: int, api_hash: str):
        self.tdjson = CDLL(tdlib_path)
        self.client_id = self._create_client()
        self._initialize(api_id, api_hash)

    def _create_client(self) -> int:
        _td_create_client_id = self.tdjson.td_create_client_id
        _td_create_client_id.restype = c_int
        return _td_create_client_id()

    def _initialize(self, api_id: int, api_hash: str):
        self.tdjson.td_set_log_message_callback.argtypes = [c_int, c_char_p]
        self.tdjson.td_set_log_message_callback(2, self._on_log_message)

        self._send({
            "@type": "setTdlibParameters",
            "database_directory": "tdlib",
            "use_message_database": True,
            "use_secret_chats": True,
            "api_id": api_id,
            "api_hash": api_hash,
            "system_language_code": "en",
            "device_model": "Desktop",
            "application_version": "1.0"
        })

    def _on_log_message(self, verbosity_level, message):
        if verbosity_level == 0:
            sys.exit(f"TDLib fatal error: {message}")

    def _send(self, query: dict):
        query_json = json.dumps(query).encode("utf-8")
        self.tdjson.td_send(self.client_id, query_json)

    def _receive(self) -> dict:
        result = self.tdjson.td_receive(1.0)
        if result:
            return json.loads(result.decode("utf-8"))
        return {}

    def execute(self, query: dict) -> dict:
        query_json = json.dumps(query).encode("utf-8")
        result = self.tdjson.td_execute(query_json)
        if result:
            return json.loads(result.decode("utf-8"))
        return {}

    def get_groups_in_common(self, user_id: int, offset_chat_id: int = 0, limit: int = 100) -> list:
        query = {
            "@type": "getGroupsInCommon",
            "user_id": user_id,
            "offset_chat_id": offset_chat_id,
            "limit": limit
        }
        return self.execute(query).get("groups", [])
