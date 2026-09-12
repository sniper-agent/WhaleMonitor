import json
import os
import time
import requests
from config import HELIUS_API_KEY
from wallets import load_wallets
from telegram_bot import send_telegram

STATE_FILE = r"E:\WhaleMonitor\data\solana_state.json"
RPC = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
PARSE = f"https://api.helius.xyz/v0/transactions/?api-key={HELIUS_API_KEY}"

def rpc(method, params):
    r = requests.post(
        RPC,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data.get("result")

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def solana_wallets():
    items = [w for w in load_wallets().values() if w["chain"] == "solana"]
    items.sort(key=lambda x: x["score"], reverse=True)
    return items[:8]

def latest_sigs(address, limit=3):
    result = rpc("getSignaturesForAddress", [address, {"limit": limit}])
    return result or []

def parse_tx(signature):
    r = requests.post(PARSE, json={"transactions": [signature]}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data:
        return None
    return data[0]

def summarize(wallet, parsed):
    buys = []
    sells = []
    wallet_l = wallet.lower()
    for t in parsed.get("tokenTransfers", []) or []:
        mint = t.get("mint", "")
        amount = t.get("tokenAmount", "")
        frm = (t.get("fromUserAccount") or "").lower()
        to = (t.get("toUserAccount") or "").lower()
        if to == wallet_l:
            buys.append(f"{amount} {mint}")
        elif frm == wallet_l:
            sells.append(f"{amount} {mint}")
    return buys, sells

def run_once():
    if not HELIUS_API_KEY:
        print("HELIUS_API_KEY kosong.")
        return
    state = load_state()
    watched = solana_wallets()
    print("Memantau", len(watched), "wallet Solana teratas")
    for w in watched:
        addr = w["address"]
        try:
            sigs = latest_sigs(addr)
        except Exception as e:
            print("Gagal", addr[:8], e)
            continue
        if not sigs:
            continue
        newest = sigs[0]["signature"]
        old = state.get(addr)
        if old is None:
            state[addr] = newest
            print("Baseline", addr[:8])
            continue
        baru = []
        for item in sigs:
            if item["signature"] == old:
                break
            baru.append(item["signature"])
        for sig in reversed(baru):
            parsed = None
            try:
                parsed = parse_tx(sig)
            except Exception as e:
                print("Gagal parse", sig[:8], e)
            buys, sells = ([], [])
            if parsed:
                buys, sells = summarize(addr, parsed)
            if buys and not sells:
                side = "BUY"
            elif sells and not buys:
                side = "SELL"
            elif buys and sells:
                side = "SWAP/CAMPUR"
            else:
                side = "TX LAIN"
            msg = (
                "WHALE SOLANA\n"
                f"Side: {side}\n"
                f"Wallet: {addr}\n"
                f"Skor: {w['score']} | muncul {w['count']} kali\n"
                f"Beli token: {buys or '-'}\n"
                f"Jual token: {sells or '-'}\n"
                f"Tx: https://solscan.io/tx/{sig}"
            )
            print(msg)
            send_telegram(msg)
        if newest:
            state[addr] = newest
    save_state(state)

def run_loop():
    print("Solana monitor jalan. Tutup dengan Ctrl+C")
    while True:
        run_once()
        time.sleep(30)