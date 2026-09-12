import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "")

MASTER_CSV = r"E:\WhaleMonitor\data\whale_wallet_master.csv"