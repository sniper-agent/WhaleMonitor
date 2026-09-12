import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

url = f"https://api.telegram.org/bot{token}/sendMessage"
pesan = "WhaleMonitor tes: bot berhasil kirim ke channel."

r = requests.post(url, data={"chat_id": chat_id, "text": pesan})
print("Status:", r.status_code)
print(r.text)