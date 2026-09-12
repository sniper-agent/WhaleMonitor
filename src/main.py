from signal_engine import score_events
from telegram_bot import send_telegram

events = [
    {"wallet": "0x055a3b37957bfbd3345bed9968e7e8dd56d67066", "side": "BUY"},
    {"wallet": "3AWDTDGZiW8joyfA52LKL7GUWLoKBCBUBLUE5JoWgBCu", "side": "BUY"},
    {"wallet": "55NQkFDwwW8noThkL9Rd5ngbgUU36fYZeos1k5ZwjGdn", "side": "BUY"},
    {"wallet": "8zFZHuSRuDpuAR7J6FzwyF3vKNx4CVW3DFHJerQhc7Zd", "side": "SELL"},
]

hasil = score_events(events)
print(hasil["text"])
ok = send_telegram(hasil["text"])
print("Terkirim ke channel:" , ok)