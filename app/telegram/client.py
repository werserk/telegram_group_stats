import base64
import json
import logging
import time
from typing import Any, Dict, Optional, Union

import app.telegram.functional as F
from app.constants import LOGIN_REPEAT_REQUEST_COUNT, AuthorizationState

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TDLibClient:
    """Handles non-blocking communication with TDLib and step-by-step authorization."""

    def __init__(
        self,
        api_id: str,
        api_hash: str,
        database_encryption_key: Union[str, bytes] = b"",
        files_directory: str = "tdlib",
        verbosity_level: int = 2,
        use_test_dc: bool = False,
        system_language_code: str = "en",
        device_model: str = "Desktop",
        system_version: str = "Unknown",
        application_version: str = "1.0",
        use_message_database: bool = True,
        use_secret_chats: bool = False,
    ) -> None:
        if isinstance(database_encryption_key, str):
            database_encryption_key = database_encryption_key.encode()
        self._db_key_base64: str = base64.b64encode(database_encryption_key).decode()
        self._api_id = api_id
        self._api_hash = api_hash
        self._use_test_dc = use_test_dc
        self._files_dir = files_directory
        self._verbosity_level = verbosity_level
        self._system_language_code = system_language_code
        self._device_model = device_model
        self._system_version = system_version
        self._application_version = application_version
        self._use_message_database = use_message_database
        self._use_secret_chats = use_secret_chats
        self._authorization_state: AuthorizationState = AuthorizationState.NONE
        self._is_authorized: bool = False
        self._client_id: int = F.create_client_id()
        self._set_verbosity_level(self._verbosity_level)
        self._params_sent: bool = False
        self._encryption_key_sent: bool = False

    def _set_verbosity_level(self, level: int) -> None:
        query = {"@type": "setLogVerbosityLevel", "new_verbosity_level": level}
        self.execute(query)
        logger.debug(f"Set TDLib verbosity to {level}")

    @property
    def authorization_state(self) -> AuthorizationState:
        return self._authorization_state

    def is_authorized(self) -> bool:
        return self._is_authorized

    def send(self, data: Dict[str, Any]) -> None:
        packed = json.dumps(data).encode("utf-8")
        F.send(self._client_id, packed)
        logger.debug(f"Sent to TDLib: {data}")

    def receive(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        response = F.receive(timeout)
        if not response:
            return None
        decoded = json.loads(response.decode("utf-8"))
        logger.debug(f"Received from TDLib: {decoded}")
        return decoded

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        packed = json.dumps(data).encode("utf-8")
        result = F.execute(packed)
        if result:
            decoded = json.loads(result.decode("utf-8"))
            logger.debug(f"Executed: {data}, result: {decoded}")
            return decoded
        return {}

    def process_all_updates(self, max_iterations: int = 25) -> AuthorizationState:
        for _ in range(max_iterations):
            update = self.receive(timeout=0.5)
            if update is None:
                break
            self._process_update(update)
            if self._authorization_state in (AuthorizationState.READY, AuthorizationState.CLOSED):
                break
        return self._authorization_state

    def _process_update(self, update: Dict[str, Any]) -> None:
        update_type = update.get("@type")
        if update_type == "updateAuthorizationState":
            new_state_type = update["authorization_state"]["@type"]
            self._handle_authorization_state(AuthorizationState(new_state_type))
        elif update_type == "error":
            logger.error(f"TDLib error: {update}")
        else:
            logger.debug(f"Ignored update: {update}")

    def _handle_authorization_state(self, new_state: AuthorizationState) -> None:
        self._authorization_state = new_state
        logger.debug(f"Authorization state updated to: {new_state}")
        if new_state == AuthorizationState.WAIT_TDLIB_PARAMS:
            self._send_params()
        elif new_state == AuthorizationState.WAIT_ENCRYPTION_KEY:
            self._send_encryption_key()
        elif new_state == AuthorizationState.READY:
            self._is_authorized = True
            logger.info("Authorization state is READY")
        elif new_state == AuthorizationState.CLOSED:
            self._is_authorized = False
            logger.warning("Authorization state is CLOSED")

    def login_step(self) -> AuthorizationState:
        self.send({"@type": "getAuthorizationState"})
        previous_state = self._authorization_state
        for _ in range(LOGIN_REPEAT_REQUEST_COUNT):
            current_state = self.process_all_updates()
            if current_state != previous_state:
                break
            time.sleep(0.1)
        return self._authorization_state

    def send_phone_number(self, phone_number: str) -> AuthorizationState:
        logger.debug(f"Sending phone number: {phone_number}")
        query = {
            "@type": "setAuthenticationPhoneNumber",
            "phone_number": phone_number,
            "allow_flash_call": False,
            "is_current_phone_number": True,
        }
        self.send(query)
        return self.login_step()

    def send_code(self, code: str) -> AuthorizationState:
        logger.debug(f"Sending code: {code}")
        query = {"@type": "checkAuthenticationCode", "code": code}
        self.send(query)
        return self.login_step()

    def send_password(self, password: str) -> AuthorizationState:
        logger.debug("Sending 2FA password")
        query = {"@type": "checkAuthenticationPassword", "password": password}
        self.send(query)
        return self.login_step()

    def close(self) -> None:
        logger.info("Closing TDLib client")
        self.send({"@type": "close"})
        for _ in range(LOGIN_REPEAT_REQUEST_COUNT):
            if self._authorization_state == AuthorizationState.CLOSED:
                break
            update = self.receive(timeout=0.2)
            if update:
                self._process_update(update)
        logger.info("TDLib client closed")

    def _send_params(self) -> None:
        if self._params_sent:
            return
        query = {
            "@type": "setTdlibParameters",
            "database_directory": self._files_dir,
            "files_directory": self._files_dir,
            "use_test_dc": self._use_test_dc,
            "api_id": int(self._api_id),
            "api_hash": self._api_hash,
            "device_model": self._device_model,
            "system_version": self._system_version,
            "application_version": self._application_version,
            "system_language_code": self._system_language_code,
            "use_message_database": self._use_message_database,
            "use_secret_chats": self._use_secret_chats,
            "database_encryption_key": self._db_key_base64,
        }
        self.send(query)
        self._params_sent = True
        logger.info("TDLib parameters sent")

    def _send_encryption_key(self) -> None:
        if self._encryption_key_sent:
            return
        query = {"@type": "checkDatabaseEncryptionKey", "encryption_key": self._db_key_base64}
        self.send(query)
        self._encryption_key_sent = True
        logger.info("Database encryption key sent")
