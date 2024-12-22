import base64
import enum
import json
import logging
import time
from typing import Any, Dict, Optional, Union

from dotenv import load_dotenv

import app.telegram.functional as F  # Ваши обёртки над tdjson/клиентом

logger = logging.getLogger(__name__)


class AuthorizationState(enum.Enum):
    NONE = None
    WAIT_TDLIB_PARAMS = "authorizationStateWaitTdlibParameters"
    WAIT_ENCRYPTION_KEY = "authorizationStateWaitEncryptionKey"
    WAIT_PHONE_NUMBER = "authorizationStateWaitPhoneNumber"
    WAIT_CODE = "authorizationStateWaitCode"
    WAIT_PASSWORD = "authorizationStateWaitPassword"
    WAIT_REGISTRATION = "authorizationStateWaitRegistration"  # вдруг пригодится
    READY = "authorizationStateReady"
    CLOSED = "authorizationStateClosed"


class TDLibClient:
    """
    Простой, неблокирующий клиент для TDLib.
    Использует пошаговую авторизацию, без бесконечных циклов и ввода через консоль.
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
        load_dotenv()  # Если нужно подгружать .env

        if isinstance(database_encryption_key, str):
            database_encryption_key = database_encryption_key.encode()
        # TDLib с 1.8.6 умеет принимать base64-encoded ключ
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

        # Сразу установим уровень логирования
        self._set_verbosity_level(self._verbosity_level)

    def _set_verbosity_level(self, level: int) -> None:
        query = {
            "@type": "setLogVerbosityLevel",
            "new_verbosity_level": level,
        }
        self.execute(query)

    def send(self, data: Dict[str, Any]) -> None:
        """
        Отправляет сырые данные в TDLib через F.send
        """
        packed = json.dumps(data).encode("utf-8")
        F.send(self._client_id, packed)

    def receive(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Однократный вызов F.receive. Возвращает update или None, если за timeout ничего не пришло.
        """
        response = F.receive(timeout)
        if not response:
            return None
        decoded = json.loads(response.decode("utf-8"))
        return decoded

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Синхронный вызов (execute).
        """
        packed = json.dumps(data).encode("utf-8")
        result = F.execute(packed)
        if result:
            return json.loads(result.decode("utf-8"))
        return {}

    def get_authorization_state(self) -> AuthorizationState:
        """
        Посылаем getAuthorizationState и пытаемся один раз прочитать ответ.
        Если получили updateAuthorizationState — обновляем self._authorization_state.
        Возвращаем текущее состояние (или если ничего не пришло — старое).
        """
        self.send({"@type": "getAuthorizationState"})
        update = self.receive()
        self._process_update(update)
        return self._authorization_state

    def _process_update(self, update: Optional[Dict[str, Any]]) -> None:
        """
        Служебный метод. Если это updateAuthorizationState, обработаем.
        Если это ошибка — залогируем. И так далее.
        """
        if not update:
            return

        if update["@type"] == "updateAuthorizationState":
            new_state = update["authorization_state"]["@type"]
            self._handle_authorization_state(new_state)

        elif update["@type"] == "error":
            logger.error(f"TDLib error: {update}")

    def _handle_authorization_state(self, new_state_str: str) -> None:
        """
        Обновляет self._authorization_state, при необходимости выполняет действия:
        - setTdlibParameters при WAIT_TDLIB_PARAMS
        - checkDatabaseEncryptionKey при WAIT_ENCRYPTION_KEY
        - выставляет self._is_authorized = True при READY
        """
        new_state = AuthorizationState(new_state_str)
        self._authorization_state = new_state

        if new_state == AuthorizationState.WAIT_TDLIB_PARAMS:
            # Отправляем параметры
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
                # Для tdlib >= 1.8.6
                "database_encryption_key": self._db_key_base64,
            }
            self.send(params_query)

        elif new_state == AuthorizationState.WAIT_ENCRYPTION_KEY:
            # Отправляем ключ
            self.send(
                {
                    "@type": "checkDatabaseEncryptionKey",
                    "encryption_key": self._db_key_base64,
                }
            )

        elif new_state == AuthorizationState.READY:
            self._is_authorized = True

        elif new_state == AuthorizationState.CLOSED:
            self._is_authorized = False

    def login_step(self) -> AuthorizationState:
        """
        «Полушаг» авторизации: мы проверяем текущее состояние (getAuthorizationState),
        если нужно — отправляем/обрабатываем update.
        Возвращаем актуальное состояние (может быть READY, WAIT_PHONE_NUMBER и т.д.).
        """
        return self.get_authorization_state()

    def send_phone_number(self, phone_number: str) -> AuthorizationState:
        """
        Отправляем номер телефона (если мы в WAIT_PHONE_NUMBER).
        После отправки, читаем update, возвращаем новое состояние.
        """
        query = {
            "@type": "setAuthenticationPhoneNumber",
            "phone_number": phone_number,
            "allow_flash_call": False,
            "is_current_phone_number": True,
        }
        self.send(query)
        update = self.receive()
        self._process_update(update)
        return self._authorization_state

    def send_code(self, code: str) -> AuthorizationState:
        """
        Отправляем код (если мы в WAIT_CODE).
        """
        query = {
            "@type": "checkAuthenticationCode",
            "code": code,
        }
        self.send(query)
        update = self.receive()
        self._process_update(update)
        return self._authorization_state

    def send_password(self, password: str) -> AuthorizationState:
        """
        Отправляем 2FA-пароль (если мы в WAIT_PASSWORD).
        """
        query = {
            "@type": "checkAuthenticationPassword",
            "password": password,
        }
        self.send(query)
        update = self.receive()
        self._process_update(update)
        return self._authorization_state

    def is_authorized(self) -> bool:
        return self._is_authorized

    def close(self) -> None:
        """
        Явно закрыть сессию. Уйдём в authorizationStateClosed.
        """
        self.send({"@type": "close"})
        # Можем дождаться, пока state станет CLOSED
        for _ in range(5):
            if self._authorization_state == AuthorizationState.CLOSED:
                break
            update = self.receive()
            self._process_update(update)
            time.sleep(0.2)
        logger.info("TDLib client closed.")
