import base64
import json
import logging
import time
from typing import Any, Dict, Optional, Union

import app.telegram.functional as F
from app.telegram.constants import AuthorizationState

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TDLibClient:
    """
    Неблокирующий клиент для TDLib с пошаговой авторизацией.
    """

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
        # TDLib с 1.8.6 принимает base64-encoded ключ
        self._db_key_base64 = base64.b64encode(database_encryption_key).decode()

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

        # Управление состояниями
        self._authorization_state: AuthorizationState = AuthorizationState.NONE
        self._is_authorized = False

        # ID клиента (созданный через ваш F.create_client_id())
        self._client_id = F.create_client_id()

        # Установим уровень логирования
        self._set_verbosity_level(self._verbosity_level)

        # Флаги для предотвращения повторной отправки параметров и ключа
        self._params_sent = False
        self._encryption_key_sent = False

    def _set_verbosity_level(self, level: int) -> None:
        query = {
            "@type": "setLogVerbosityLevel",
            "new_verbosity_level": level,
        }
        self.execute(query)
        logger.debug(f"Set TDLib verbosity level to {level}")

    def send(self, data: Dict[str, Any]) -> None:
        """
        Отправляет сырые данные в TDLib через F.send
        """
        packed = json.dumps(data).encode("utf-8")
        F.send(self._client_id, packed)
        logger.debug(f"Sent to TDLib: {data}")

    def send_params(self) -> None:
        """
        Отправляет запрос на установку параметров TDLib.
        """
        if self._params_sent:
            logger.debug("Parameters already sent, skipping.")
            return
        params_query = {
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
        self.send(params_query)
        self._params_sent = True
        logger.info("Sent setTdlibParameters to TDLib.")

    def send_encryption_key(self) -> None:
        """
        Отправляет запрос на проверку базы данных.
        """
        if self._encryption_key_sent:
            logger.debug("Encryption key already sent, skipping.")
            return
        encryption_key_query = {"@type": "checkDatabaseEncryptionKey", "encryption_key": self._db_key_base64}
        self.send(encryption_key_query)
        self._encryption_key_sent = True
        logger.info("Sent checkDatabaseEncryptionKey to TDLib.")

    def receive(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Однократный вызов F.receive. Возвращает update или None, если за timeout ничего не пришло.
        """
        response = F.receive(timeout)
        if not response:
            logger.debug("Receive timed out with no response.")
            return None
        decoded = json.loads(response.decode("utf-8"))
        logger.debug(f"Received from TDLib: {decoded}")
        return decoded

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Синхронный вызов (execute).
        """
        packed = json.dumps(data).encode("utf-8")
        result = F.execute(packed)
        if result:
            decoded = json.loads(result.decode("utf-8"))
            logger.debug(f"Executed TDLib command: {data}, Result: {decoded}")
            return decoded
        logger.debug(f"Executed TDLib command: {data}, No result returned.")
        return {}

    def _process_update(self, update: Optional[Dict[str, Any]]) -> None:
        """
        Обрабатывает апдейты от TDLib.
        """
        if not update:
            return

        if update["@type"] == "updateAuthorizationState":
            new_state = update["authorization_state"]["@type"]
            logger.debug(f"Authorization state updated to: {new_state}")
            self._handle_authorization_state(new_state)
        elif update["@type"] == "error":
            logger.error(f"TDLib error: {update}")
        else:
            logger.debug(f"Ignored TDLib update: {update}")

    def _handle_authorization_state(self, new_state_str: str) -> None:
        """
        Обрабатывает новое состояние авторизации.
        """
        new_state = AuthorizationState(new_state_str)
        self._authorization_state = new_state

        if new_state == AuthorizationState.WAIT_TDLIB_PARAMS:
            # Отправляем параметры
            self.send_params()

        elif new_state == AuthorizationState.WAIT_ENCRYPTION_KEY:
            # Отправляем ключ
            self.send_encryption_key()

        elif new_state == AuthorizationState.READY:
            self._is_authorized = True
            logger.info("Authorization state is READY.")

        elif new_state == AuthorizationState.CLOSED:
            self._is_authorized = False
            logger.warning("Authorization state is CLOSED.")

    def process_all_updates(self, max_iterations: int = 20) -> AuthorizationState:
        """
        Обрабатывает все доступные апдейты.
        """
        for _ in range(max_iterations):
            update = self.receive(timeout=0.5)
            if not update:
                break
            self._process_update(update)
            # Выход из цикла, если авторизация завершена
            if self._authorization_state in [AuthorizationState.READY, AuthorizationState.CLOSED]:
                break
        return self._authorization_state

    def login_step(self) -> AuthorizationState:
        """
        Один шаг авторизации: запрашивает текущее состояние и обрабатывает все доступные апдейты.
        """
        logger.debug("Starting login_step.")
        self.send({"@type": "getAuthorizationState"})
        previous_state = self._authorization_state

        # Обрабатываем все апдейты, пока состояние не изменится или пока не достигнем лимита
        current_state = previous_state
        for _ in range(10):
            current_state = self.process_all_updates()
            if current_state != previous_state:
                logger.debug(f"Authorization state changed from {previous_state} to {current_state}")
                break
            time.sleep(0.1)
        logger.debug(f"login_step completed. Current state: {current_state}")
        return current_state

    def send_phone_number(self, phone_number: str) -> AuthorizationState:
        """
        Отправляет номер телефона и обрабатывает апдейты.
        """
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
        """
        Отправляет код авторизации и обрабатывает апдейты.
        """
        logger.debug(f"Sending code: {code}")
        query = {
            "@type": "checkAuthenticationCode",
            "code": code,
        }
        self.send(query)
        return self.login_step()

    def send_password(self, password: str) -> AuthorizationState:
        """
        Отправляет пароль 2FA и обрабатывает апдейты.
        """
        logger.debug("Sending password.")
        query = {
            "@type": "checkAuthenticationPassword",
            "password": password,
        }
        self.send(query)
        return self.login_step()

    def is_authorized(self) -> bool:
        """
        Возвращает статус авторизации.
        """
        return self._is_authorized

    def close(self) -> None:
        """
        Закрывает сессию.
        """
        logger.info("Closing TDLib client.")
        self.send({"@type": "close"})
        # Можно дождаться состояния CLOSED, если необходимо
        for _ in range(10):
            if self._authorization_state == AuthorizationState.CLOSED:
                break
            update = self.receive()
            self._process_update(update)
            time.sleep(0.2)
        logger.info("TDLib client closed.")
