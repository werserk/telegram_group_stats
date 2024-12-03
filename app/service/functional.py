import os
import sys
from ctypes import *

# load shared library
tdjson_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "libtdjson.so")
tdjson = CDLL(tdjson_path)

# load TDLib functions from shared library
create_client_id = tdjson.td_create_client_id
create_client_id.restype = c_int
create_client_id.argtypes = []

receive = tdjson.td_receive
receive.restype = c_char_p
receive.argtypes = [c_double]

send = tdjson.td_send
send.restype = None
send.argtypes = [c_int, c_char_p]

execute = tdjson.td_execute
execute.restype = c_char_p
execute.argtypes = [c_char_p]

log_message_callback_type = CFUNCTYPE(None, c_int, c_char_p)

set_log_message_callback = tdjson.td_set_log_message_callback
set_log_message_callback.restype = None
set_log_message_callback.argtypes = [c_int, log_message_callback_type]


# initialize TDLib log with desired parameters
@log_message_callback_type
def on_log_message_callback(verbosity_level, message):
    if verbosity_level == 0:
        sys.exit("TDLib fatal error: %r" % message)


set_log_message_callback(2, on_log_message_callback)
