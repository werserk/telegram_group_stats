from enum import Enum


class AuthorizationState(str, Enum):
    WAIT_TDLIB_PARAMS = "authorizationStateWaitTdlibParameters"
    WAIT_ENCRYPTION_KEY = "authorizationStateWaitEncryptionKey"
    WAIT_PHONE = "authorizationStateWaitPhoneNumber"
    WAIT_CODE = "authorizationStateWaitCode"
    WAIT_PASSWORD = "authorizationStateWaitPassword"
    READY = "authorizationStateReady"
    CLOSED = "authorizationStateClosed"
