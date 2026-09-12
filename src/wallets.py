import csv
from config import MASTER_CSV

def load_wallets():
    data = {}
    with open(MASTER_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            addr = row["wallet_normalized"].strip()
            data[addr.lower()] = {
                "address": addr,
                "chain": row["chain"],
                "count": int(row["top10_count"]),
                "score": int(row["score"]),
                "tokens": row["tokens"],
                "stars": int(row["top10_count"]),
            }
    return data

def star_text(count):
    if count >= 3:
        return "B3"
    if count == 2:
        return "B2"
    return "B1"