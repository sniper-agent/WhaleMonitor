import json
import os
import time
import requests
from config import HELIUS_API_KEY
from wallets import load_wallets
from signal_engine import add_event, flush_alerts
from token_stats import token_stats, usd_value

STATE_FILE = r"E:\WhaleMonitor\data\solana_state.json"
RPC = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
PARSE = f"https://api.helius.xyz/v0/transactions/?api-key={HELIUS_API_KEY}"

QUOTE = {
    "so11111111111111111111111111111111111111112": "SOL",
    "epjfwdd5aufqssqem2qn1xzybapc8g4weggkzwydt1v": "USDC",
    "es9vmfrzacermjfrf4h2fyd4kconky11mcce8benwnyb": "USDT",
}

symbol_cache = {}

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

def token_name(mint):
    key = mint.lower()
    if key in QUOTE:
        return QUOTE[key]
    if key in symbol_cache:
        return symbol_cache[key]
    try:
        asset = rpc("getAsset", {"id": mint})
        symbol = (
            (((asset or {}).get("content") or {}).get("metadata") or {}).get("symbol")
            or mint[:6] + "..."
        )
    except Exception:
        symbol = mint[:6] + "..."
    symbol_cache[key] = symbol
    return symbol

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
    return items

def latest_sigs(address, limit=3):
    return rpc("getSignaturesForAddress", [address, {"limit": limit}]) or []

def parse_tx(signature):
    r = requests.post(PARSE, json={"transactions": [signature]}, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data[0] if data else None

def net_tokens(wallet, parsed):
    wallet_l = wallet.lower()
    net = {}
    for t in parsed.get("tokenTransfers", []) or []:
        mint = t.get("mint") or ""
        if not mint:
            continue
        try:
            amount = float(t.get("tokenAmount") or 0)
        except Exception:
            continue
        frm = (t.get("fromUserAccount") or "").lower()
        to = (t.get("toUserAccount") or "").lower()
        if to == wallet_l:
            net[mint] = net.get(mint, 0) + amount
        elif frm == wallet_l:
            net[mint] = net.get(mint, 0) - amount
    return net

def is_swap(parsed):
    tipe = (parsed.get("type") or "").upper()
    sumber = (parsed.get("source") or "").upper()
    desc = (parsed.get("description") or "").lower()
    if tipe in {"TRANSFER", "NFT_SALE", "NFT_LISTING", "COMPRESSED_NFT"}:
        return False
    if "swap" in desc or tipe == "SWAP":
        return True
    if sumber in {"JUPITER", "RAYDIUM", "ORCA", "PUMP_FUN", "METEORA"}:
        return True
    return False

def format_swap(wallet, parsed):
    net = net_tokens(wallet, parsed)
    received = []
    sent = []
    for mint, amount in net.items():
        if abs(amount) < 1e-9:
            continue
        name = token_name(mint)
        item = {
            "name": name,
            "mint": mint,
            "amount": amount,
            "quote": mint.lower() in QUOTE,
        }
        if amount > 0:
            received.append(item)
        else:
            item["amount"] = abs(amount)
            sent.append(item)

    recv_meme = [x for x in received if not x["quote"]]
    sent_meme = [x for x in sent if not x["quote"]]
    recv_quote = [x for x in received if x["quote"]]
    sent_quote = [x for x in sent if x["quote"]]

    if recv_meme and sent_quote:
        side, token, paid = "BUY", recv_meme[0], sent_quote[0]
    elif sent_meme and recv_quote:
        side, token, paid = "SELL", sent_meme[0], recv_quote[0]
    else:
        return None

    return {
        "chain": "solana",
        "side": side,
        "token": token["name"],
        "ca": token["mint"],
        "amount": token["amount"],
        "paid": f"{paid['amount']} {paid['name']}",
        "wallet": wallet,
        "tx": parsed.get("signature", ""),
    }

def handle_large_transfer(wallet, parsed, sig):
    net = net_tokens(wallet, parsed)
    for mint, amount in net.items():
        if mint.lower() in QUOTE:
            continue
        if abs(amount) < 1e-9:
            continue
        st = token_stats("solana", mint)
        nilai = usd_value(abs(amount), st.get("price_usd"))
        if nilai < 10000:
            continue
        add_event({
            "chain": "solana",
            "side": "IN" if amount > 0 else "OUT",
            "token": token_name(mint),
            "ca": mint,
            "amount": abs(amount),
            "paid": f"${nilai:,.0f}",
            "wallet": wallet,
            "tx": sig,
            "kind": "LARGE_TRANSFER",
        })

def run_once():
    if not HELIUS_API_KEY:
        print("HELIUS_API_KEY kosong.")
        return
    state = load_state()
    watched = solana_wallets()
    print("Memantau", len(watched), "wallet Solana")
    for w in watched:
        addr = w["address"]
        try:
            sigs = latest_sigs(addr)
        except Exception as e:
            print("Gagal", addr[:8], e)
            time.sleep(0.2)
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
            try:
                parsed = parse_tx(sig)
            except Exception as e:
                print("Gagal parse", sig[:8], e)
                continue
            if not parsed:
                continue
            if is_swap(parsed):
                msg = format_swap(addr, parsed)
                if msg:
                    print("SWAP", msg["side"], msg["token"], addr[:8])
                    add_event(msg)
            else:
                handle_large_transfer(addr, parsed, sig)
        state[addr] = newest
        time.sleep(0.15)
    save_state(state)
    flush_alerts("solana")

def run_loop():
    print("Solana live + saringan sinyal. Ctrl+C untuk berhenti")
    while True:
        run_once()
        time.sleep(60)