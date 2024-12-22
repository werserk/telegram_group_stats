import streamlit as st

from app.telegram.client import AuthorizationState, TDLibClient


class AuthorizePage:
    def __init__(self, td_client: TDLibClient):
        self.td_client = td_client

    def show(self):
        st.title("Telegram Authorization")

        if "auth_state" not in st.session_state:
            # Первый вызов авторизации
            st.session_state["auth_state"] = self.td_client.login_step()

        current_state = st.session_state["auth_state"]

        st.write(f"Current authorization state: `{current_state.value}`")

        if current_state == AuthorizationState.READY:
            st.success("You are already authorized! Go to Analytics.")
            return

        if st.button("Refresh State"):
            # Обрабатываем все апдейты
            st.session_state["auth_state"] = self.td_client.login_step()
            st.rerun()

        # Отображаем поля ввода в зависимости от состояния
        if current_state == AuthorizationState.WAIT_PHONE_NUMBER:
            self._show_phone_input()
        elif current_state == AuthorizationState.WAIT_CODE:
            self._show_code_input()
        elif current_state == AuthorizationState.WAIT_PASSWORD:
            self._show_password_input()
        elif current_state == AuthorizationState.WAIT_TDLIB_PARAMS:
            # Клиент автоматически отправляет setTdlibParameters
            st.info("TDLib parameters are being set. Press Refresh to check the state.")
        elif current_state == AuthorizationState.WAIT_ENCRYPTION_KEY:
            # Клиент автоматически отправляет checkDatabaseEncryptionKey
            st.info("Checking DB encryption key. Press Refresh to check the state.")
        elif current_state == AuthorizationState.CLOSED:
            st.error("TDLib is closed. Restart the app or check logs.")
        elif current_state == AuthorizationState.WAIT_REGISTRATION:
            st.info("User registration is required. Implement registration steps if needed.")

    def _show_phone_input(self):
        phone_number = st.text_input("Enter your phone number:", value="", key="phone_input")
        if st.button("Send phone number"):
            if phone_number:
                st.session_state["auth_state"] = self.td_client.send_phone_number(phone_number)
                st.rerun()
            else:
                st.warning("Please enter a valid phone number.")

    def _show_code_input(self):
        code = st.text_input("Enter the code from Telegram/SMS:", value="", key="code_input")
        if st.button("Send code"):
            if code:
                st.session_state["auth_state"] = self.td_client.send_code(code)
                st.rerun()
            else:
                st.warning("Please enter the code you received.")

    def _show_password_input(self):
        password = st.text_input("Enter your 2FA password:", type="password", key="password_input")
        if st.button("Send password"):
            if password:
                st.session_state["auth_state"] = self.td_client.send_password(password)
                st.rerun()
            else:
                st.warning("Please enter your password.")
