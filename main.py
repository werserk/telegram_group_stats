import os

from dotenv import load_dotenv

from app.service.client import TDLibClient

load_dotenv()


def main():
    tdlib_client = TDLibClient(api_id=os.getenv("API_ID"), api_hash=os.getenv("API_HASH"))


if __name__ == "__main__":
    main()
