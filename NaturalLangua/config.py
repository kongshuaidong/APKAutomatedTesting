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

# ── 飞书自建应用机器人（用于测试结果私聊通知，可选）─────────────────
# 未配置则跳过发送，不影响测试执行
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_RECEIVE_ID = os.getenv("FEISHU_RECEIVE_ID", "")
# receive_id_type: email / open_id / user_id / union_id / phone / chat_id
FEISHU_RECEIVE_ID_TYPE = os.getenv("FEISHU_RECEIVE_ID_TYPE", "email")
