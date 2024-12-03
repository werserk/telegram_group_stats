import json
from typing import Dict

import app.service.functional as F


class TDLibClient:
    def __init__(self, api_id: str, api_hash: str):
        self.client_id = F.create_client_id()
        self.authorize(api_id, api_hash)

    def authorize(self, api_id: str, api_hash: str) -> None:
        self.send(
            {
                "@type": "setTdlibParameters",
                "database_directory": "tdlib",
                "use_message_database": True,
                "use_secret_chats": True,
                "api_id": api_id,
                "api_hash": api_hash,
                "system_language_code": "en",
                "device_model": "Desktop",
                "application_version": "1.0",
            }
        )

    @staticmethod
    def execute(query: Dict) -> Dict:
        query = json.dumps(query).encode("utf-8")
        result = F.execute(query)
        if result:
            result = json.loads(result.decode("utf-8"))
        return result

    @staticmethod
    def receive() -> Dict:
        result = F.receive(1.0)
        if result:
            result = json.loads(result.decode("utf-8"))
        return result

    def send(self, query: Dict) -> None:
        query = json.dumps(query).encode("utf-8")
        F.send(self.client_id, query)
