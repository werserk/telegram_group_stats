import json
import sys
import time
from typing import Dict

from loguru import logger

import app.service.functional as F


class TDLibClient:
    ERROR_LOG_LEVEL = 2
    RECEIVE_LOOP_TIMEOUT = 5
    AUTHORIZE_LOOP_TIMEOUT = 5

    def __init__(self, api_id: str, api_hash: str):
        self.__api_id = api_id
        self.__api_hash = api_hash
        self._client_id = F.create_client_id()
        self._set_verbosity_level(TDLibClient.ERROR_LOG_LEVEL)
        self._is_authorized = False
        self._authorize()
        time.sleep(TDLibClient.AUTHORIZE_LOOP_TIMEOUT)

    def _set_verbosity_level(self, level: int):
        self.execute({"@type": "setLogVerbosityLevel", "new_verbosity_level": level})

    def _authorize(self):
        self.send({"@type": "getAuthorizationState"})
        while not self._is_authorized:
            event = self.receive()
            if event:
                self._handle_event(event)
            else:
                time.sleep(TDLibClient.AUTHORIZE_LOOP_TIMEOUT)

    def _handle_event(self, event: Dict):
        if event["@type"] == "updateAuthorizationState":
            self._handle_auth_state(event["authorization_state"])
        elif event["@type"] == "error":
            if event["code"] == 420 and "FLOOD_WAIT" in event["message"]:
                wait_time = int(event["message"].split("_")[-1])
                logger.debug(f"Необходимо подождать {wait_time} секунд из-за ограничения запросов.")
                if input("Ожидать? [y/n]") == "y":
                    time.sleep(wait_time)
                else:
                    sys.exit()
            else:
                logger.error(f"Error: {event}")

    def _handle_auth_state(self, auth_state: Dict):
        auth_type = auth_state["@type"]
        if auth_type == "authorizationStateWaitTdlibParameters":
            self.send(
                {
                    "@type": "setTdlibParameters",
                    "use_test_dc": False,
                    "database_directory": "tdlib",
                    "files_directory": "tdlib",
                    "use_file_database": False,
                    "use_chat_info_database": False,
                    "use_message_database": False,
                    "use_secret_chats": False,
                    "api_id": self.__api_id,
                    "api_hash": self.__api_hash,
                    "system_language_code": "en",
                    "device_model": "Desktop",
                    "system_version": "Unknown",
                    "application_version": "1.0",
                    "enable_storage_optimizer": True,
                    "ignore_file_names": False,
                }
            )
        elif auth_type == "authorizationStateWaitEncryptionKey":
            self.send({"@type": "checkDatabaseEncryptionKey", "encryption_key": ""})
        elif auth_type == "authorizationStateWaitPhoneNumber":
            phone_number = input("Please enter your phone number: ")
            self.send({"@type": "setAuthenticationPhoneNumber", "phone_number": phone_number})
        elif auth_type == "authorizationStateWaitCode":
            code = input("Please enter the authentication code you received: ")
            self.send({"@type": "checkAuthenticationCode", "code": code})
        elif auth_type == "authorizationStateWaitPassword":
            password = input("Please enter your password: ")
            self.send({"@type": "checkAuthenticationPassword", "password": password})
        elif auth_type == "authorizationStateReady":
            self._is_authorized = True
            logger.info("Authorization completed successfully!")
        elif auth_type == "authorizationStateClosed":
            logger.info("Authorization state closed")
            self._is_authorized = False
        else:
            logger.error(f"Unhandled authorization state: {auth_state}")

    @staticmethod
    def execute(query: Dict) -> Dict:
        query_json = json.dumps(query).encode("utf-8")
        result = F.execute(query_json)
        if result:
            result = json.loads(result.decode("utf-8"))
        return result

    @staticmethod
    def receive() -> Dict:
        result = F.receive(TDLibClient.RECEIVE_LOOP_TIMEOUT)
        if result:
            result = json.loads(result.decode("utf-8"))
        return result

    def send(self, query: Dict) -> None:
        query_json = json.dumps(query).encode("utf-8")
        F.send(self._client_id, query_json)
