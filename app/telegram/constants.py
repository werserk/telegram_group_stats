from enum import Enum


class AuthorizationState(Enum):
    NONE = "None"
    WAIT_TDLIB_PARAMS = "authorizationStateWaitTdlibParameters"
    WAIT_ENCRYPTION_KEY = "authorizationStateWaitEncryptionKey"
    WAIT_PHONE_NUMBER = "authorizationStateWaitPhoneNumber"
    WAIT_CODE = "authorizationStateWaitCode"
    WAIT_PASSWORD = "authorizationStateWaitPassword"
    WAIT_REGISTRATION = "authorizationStateWaitRegistration"
    READY = "authorizationStateReady"
    CLOSED = "authorizationStateClosed"


class ChatType(Enum):
    BASIC_GROUP = "chatTypeBasicGroup"
    SUPERGROUP = "chatTypeSupergroup"
    PRIVATE = "chatTypePrivate"


# "Магические числа" и прочие константы
RECEIVE_LOOP_TIMEOUT = 5
MAX_COUNT_CHATS_RESPONSE = 100_000
MAX_COUNT_MEMBERS_RESPONSE = 100_000
COMMON_GROUPS_LIMIT = 100_000  # Используется в getGroupsInCommon
DOWNLOAD_PRIORITY = 1
