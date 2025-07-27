import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Settings:
    TG_TOKEN: str = os.getenv("TG_TOKEN", "")
    WEB_URL:  str = os.getenv("WEB_URL", "https://localhost:8000")
    ADMIN_IDS: List[int] = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

    def webhook(self) -> str:
        return f"{self.WEB_URL}/webhook"

settings = Settings()
