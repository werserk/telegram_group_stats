import streamlit as st

from app.telegram.client import AuthorizationState, TDLibClient


class AuthorizePage:
    def __init__(self, td_client: TDLibClient):
        self.td_client = td_client

    def show(self):
        st.title("Telegram Authorization (Non-blocking)")

        # 1) При первом заходе (или после F5) - вызовем login_step(),
        #    чтобы TDLibClient рассказал нам текущее состояние.
        if "auth_state" not in st.session_state:
            st.session_state["auth_state"] = self.td_client.login_step()

        current_state = st.session_state["auth_state"]

        st.write(f"Current authorization state: `{current_state}`")

        # 2) Если уже READY — ничего вводить не нужно.
        if current_state == AuthorizationState.READY:
            st.success("You are already authorized! Go to Analytics.")
            return

        # 3) Кнопка «Refresh State», чтобы вручную обновить состояние (получить апдейты).
        #    Это может пригодиться, когда TDLib переходит на WAIT_CODE без запроса телефона,
        #    или когда нужно «подхватить» обновления, если что-то висело.
        if st.button("Refresh State"):
            st.session_state["auth_state"] = self.td_client.login_step()
            st.rerun()

        # 4) В зависимости от состояния — показываем нужные поля.
        if current_state == AuthorizationState.WAIT_PHONE_NUMBER:
            self._show_phone_number_input()

        elif current_state == AuthorizationState.WAIT_CODE:
            self._show_code_input()

        elif current_state == AuthorizationState.WAIT_PASSWORD:
            self._show_password_input()

        elif current_state == AuthorizationState.WAIT_TDLIB_PARAMS:
            st.info("TDLib parameters are being set. Press Refresh if needed.")

        elif current_state == AuthorizationState.WAIT_ENCRYPTION_KEY:
            st.info("Check DB encryption key. Press Refresh if needed.")

        elif current_state == AuthorizationState.CLOSED:
            st.error("TDLib is closed. Restart the app or check logs.")

    def _show_phone_number_input(self):
        phone_number = st.text_input("Enter your phone number:", value="")
        if st.button("Send phone number"):
            new_state = self.td_client.send_phone_number(phone_number)
            st.session_state["auth_state"] = new_state
            st.rerun()

    def _show_code_input(self):
        code = st.text_input("Enter the code from SMS:", value="")
        if st.button("Send code"):
            new_state = self.td_client.send_code(code)
            st.session_state["auth_state"] = new_state
            st.rerun()

    def _show_password_input(self):
        password = st.text_input("Enter your 2FA password:", type="password")
        if st.button("Send password"):
            new_state = self.td_client.send_password(password)
            st.session_state["auth_state"] = new_state
            st.rerun()
