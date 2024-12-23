import streamlit as st
from loguru import logger

from app.constants import KEY_AUTH_STATE, REPEAT_AUTH_REQUEST_COUNT
from app.telegram.client import AuthorizationState, TDLibClient


class AuthorizePage:
    def __init__(self, td_client: TDLibClient):
        self.td_client = td_client

    def show(self):
        st.title("Telegram Authorization")
        if KEY_AUTH_STATE not in st.session_state:
            with st.spinner("Initializing..."):
                for _ in range(REPEAT_AUTH_REQUEST_COUNT):
                    st.session_state[KEY_AUTH_STATE] = self.td_client.login_step()
            st.rerun()

        current_state = st.session_state[KEY_AUTH_STATE]
        if current_state == AuthorizationState.READY:
            st.success("You are authorized! Go to Analytics.")
            return

        if current_state == AuthorizationState.WAIT_PHONE_NUMBER:
            self._show_phone_input()
        elif current_state == AuthorizationState.WAIT_CODE:
            self._show_code_input()
        elif current_state == AuthorizationState.WAIT_PASSWORD:
            self._show_password_input()
        elif current_state == AuthorizationState.WAIT_TDLIB_PARAMS:
            st.info("TDLib parameters are being set. Press Refresh.")
        elif current_state == AuthorizationState.WAIT_ENCRYPTION_KEY:
            st.info("Checking DB encryption key. Press Refresh.")
        elif current_state == AuthorizationState.CLOSED:
            st.error("TDLib is closed.")
        elif current_state == AuthorizationState.WAIT_REGISTRATION:
            st.info("User registration required.")
        elif current_state == AuthorizationState.WAIT_CLOSING:
            st.info("TDLib is closing. Press Refresh.")
        elif current_state == AuthorizationState.CLOSED:
            st.error("TDLib is closed. Press Refresh.")

        if st.button("Refresh State"):
            st.session_state[KEY_AUTH_STATE] = self.td_client.login_step()
            logger.info(f"Authorization state refreshed: {st.session_state[KEY_AUTH_STATE]}")
            st.rerun()

    def _show_phone_input(self):
        phone_number = st.text_input("Enter your phone number:", value="", key="phone_input")
        if st.button("Send phone number"):
            if phone_number:
                st.session_state[KEY_AUTH_STATE] = self.td_client.send_phone_number(phone_number)
                st.rerun()
            else:
                st.warning("Please enter a valid phone number.")

    def _show_code_input(self):
        code = st.text_input("Enter the code:", value="", key="code_input")
        if st.button("Send code"):
            if code:
                st.session_state[KEY_AUTH_STATE] = self.td_client.send_code(code)
                st.rerun()
            else:
                st.warning("Please enter the code.")

    def _show_password_input(self):
        password = st.text_input("Enter your 2FA password:", type="password", key="password_input")
        if st.button("Send password"):
            if password:
                st.session_state[KEY_AUTH_STATE] = self.td_client.send_password(password)
                st.rerun()
            else:
                st.warning("Please enter your password.")
