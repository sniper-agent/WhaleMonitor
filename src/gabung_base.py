import csv

master = r"E:\WhaleMonitor\data\whale_wallet_master.csv"
base = r"E:\WhaleMonitor\data\base_wallet_master.csv"

with open(master, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())

existing = {(r["chain"], r["wallet_normalized"].lower()) for r in rows}

baru = 0
with open(base, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        key = (r["chain"], r["wallet_normalized"].lower())
        if key in existing:
            continue
        rows.append(r)
        existing.add(key)
        baru += 1

with open(master, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

print("Wallet baru Base ditambah:", baru)
print("Total wallet sekarang:", len(rows))