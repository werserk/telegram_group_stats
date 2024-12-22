import os

import streamlit as st
from dotenv import load_dotenv

from app.telegram.client import TDLibClient
from app.telegram.service import ChatMemberService
from app.web.analytics import AnalyticsPage
from app.web.auth import AuthorizePage

load_dotenv()


@st.cache_resource
def init_tdlib_client() -> TDLibClient:
    api_id = os.getenv("API_ID", "")
    api_hash = os.getenv("API_HASH", "")
    db_enc_key = os.getenv("DB_KEY", "")

    client = TDLibClient(
        api_id=api_id,
        api_hash=api_hash,
        database_encryption_key=db_enc_key,
        files_directory="tdlib",
        verbosity_level=2,
    )
    return client


def main() -> None:
    client = init_tdlib_client()

    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select page", ["Authorization", "Analytics"])

    if page == "Authorization":
        auth_page = AuthorizePage(client)
        auth_page.show()
    else:
        if client.is_authorized():
            service = ChatMemberService(client)
            analytics_page = AnalyticsPage(service)
            analytics_page.show()
        else:
            st.warning("Not authorized yet. Go to 'Authorization' first.")


if __name__ == "__main__":
    main()
