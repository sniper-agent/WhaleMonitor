from signal_engine import add_event, flush_alerts

events = [
    {
        "chain": "solana",
        "side": "BUY",
        "token": "ANSEM",
        "ca": "9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump",
        "amount": 115.24,
        "paid": "0.18 SOL",
        "wallet": "55NQkFDwwW8noThkL9Rd5ngbgUU36fYZeos1k5ZwjGdn",
        "tx": "tes1",
    },
    {
        "chain": "solana",
        "side": "BUY",
        "token": "ANSEM",
        "ca": "9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump",
        "amount": 80.1,
        "paid": "0.12 SOL",
        "wallet": "3AWDTDGZiW8joyfA52LKL7GUWLoKBCBUBLUE5JoWgBCu",
        "tx": "tes2",
    },
    {
        "chain": "solana",
        "side": "SELL",
        "token": "ANSEM",
        "ca": "9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump",
        "amount": 20.0,
        "paid": "0.03 SOL",
        "wallet": "8zFZHuSRuDpuAR7J6FzwyF3vKNx4CVW3DFHJerQhc7Zd",
        "tx": "tes3",
    },
]

for e in events:
    add_event(e)

flush_alerts()
print("Selesai. Harusnya 1 pesan, ada Price/LP/Market cap.")