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
