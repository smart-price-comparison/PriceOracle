import os
from dotenv import load_dotenv

load_dotenv()


def get_serpapi_api_key() -> str:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "SERPAPI_API_KEY is not set. Add it to your environment or .env file."
        )
    return api_key