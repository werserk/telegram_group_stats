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


RECEIVE_LOOP_TIMEOUT = 5
MAX_COUNT_CHATS_RESPONSE = 100_000
MAX_COUNT_MEMBERS_RESPONSE = 100_000
COMMON_GROUPS_LIMIT = 100_000
DOWNLOAD_PRIORITY = 1
LOGIN_REPEAT_REQUEST_COUNT = 10

KEY_AUTH_STATE = "auth_state"
REPEAT_AUTH_REQUEST_COUNT = 3

# Graph and UI constants
SUPERGROUP_FETCH_LIMIT = 200
GRAPH_DEFAULT_HEIGHT = "600px"
GRAPH_DEFAULT_WIDTH = "100%"
GRAPH_EDGE_WIDTH = 5
GRAPH_NODE_SIZE_BASE = 60
GRAPH_NODE_SIZE_FACTOR = 2
GRAPH_FONT_SIZE_BASE = 40
GRAPH_FONT_SIZE_FACTOR = 2
GRAPH_GROUP_SIZE_FACTOR = 3

COLOR_GRAY = "gray"
COLOR_ORANGE = "orange"
COLOR_WHITE = "white"
COLOR_BLACK = "black"
COLOR_GREEN = "green"

SHAPE_CIRCULAR_IMAGE = "circularImage"
FONT_FACE_TAHOMA = "Tahoma"
FONT_FACE_SANS = "Sans-Serif"
