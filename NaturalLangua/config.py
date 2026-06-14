import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

SCRCPY_PATH = os.getenv("SCRCPY_PATH", "scrcpy")

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
