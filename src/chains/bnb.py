import json
import os
import sys
import time
import requests

sys.path.insert(0, r"E:\WhaleMonitor\src")

from wallets import load_wallets
from signal_engine import add_event, flush_alerts

STATE_FILE = r"E:\WhaleMonitor\data\bnb_state.json"
RPCS = [
    "https://bsc-dataseed.binance.org/",
    "https://bsc-dataseed2.binance.org/",
    "https://bsc-dataseed3.binance.org/",
    "https://bsc-dataseed4.binance.org/",
    "https://binance.llamarpc.com",
    "https://bsc.publicnode.com",
    "https://1rpc.io/bnb",
]
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
WBNB = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
USDT = "0x55d398326f99059ff775485246999027b3197955"
USDC = "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"
QUOTE = {WBNB, USDT, USDC}
LARGE_USD = 10000
SLEEP_WALLET = 1.0
LOOP_SLEEP = 30
MAX_RANGE = 30

rpc_i = 0


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def bnb_wallets():
    items = [w for w in load_wallets().values() if w["chain"] == "bnb"]
    items.sort(key=lambda x: x["score"], reverse=True)
    return items


def rpc(method, params):
    global rpc_i
    last = None
    for _ in range(len(RPCS)):
        url = RPCS[rpc_i % len(RPCS)]
        rpc_i += 1
        try:
            r = requests.post(
                url,
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                timeout=20,
            )
            data = r.json()
            err = data.get("error")
            if err:
                msg = str(err.get("message") or err).lower()
                if "limit" in msg or err.get("code") == -32005:
                    print("BNB limit, ganti RPC")
                    time.sleep(3)
                    last = err
                    continue
                raise RuntimeError(err)
            return data.get("result")
        except Exception as e:
            print("Ganti RPC", str(e)[:60])
            last = e
            time.sleep(1)
    raise RuntimeError(last)


def hex_int(v):
    return int(v, 16)


def pad_addr(addr):
    return "0x" + addr.lower().replace("0x", "").zfill(64)


def topic_addr(topic):
    return "0x" + topic[-40:].lower()


def latest_block():
    return hex_int(rpc("eth_blockNumber", []))


def get_logs(from_block, to_block, topic1=None, topic2=None):
    return rpc("eth_getLogs", [{
        "fromBlock": hex(from_block),
        "toBlock": hex(to_block),
        "topics": [TRANSFER_TOPIC, topic1, topic2],
    }]) or []


def bnb_price():
    try:
        r = requests.get(
            "https://api.dexscreener.com/tokens/v1/bsc/0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
            timeout=10,
        )
        pairs = r.json()
        if isinstance(pairs, list) and pairs:
            return float(pairs[0].get("priceUsd") or 0)
    except Exception:
        pass
    return 600.0


def run_once():
    state = load_state()
    watched = bnb_wallets()
    print("Memantau", len(watched), "wallet BNB")
    now_block = latest_block()
    px = bnb_price()
    ada = 0
    for w in watched:
        addr = w["address"]
        key = addr.lower()
        old = state.get(key)
        if old is None:
            state[key] = now_block
            print("Baseline", addr[:10], "blok", now_block)
            time.sleep(SLEEP_WALLET)
            continue
        try:
            start = int(old) + 1
        except Exception:
            start = now_block
        if now_block - start > MAX_RANGE:
            start = now_block - MAX_RANGE
        if start > now_block:
            time.sleep(SLEEP_WALLET)
            continue
        topic = pad_addr(addr)
        logs = []
        try:
            logs.extend(get_logs(start, now_block, topic1=topic, topic2=None))
            time.sleep(0.3)
            logs.extend(get_logs(start, now_block, topic1=None, topic2=topic))
        except Exception as e:
            print("Gagal log", addr[:10], e)
            time.sleep(SLEEP_WALLET)
            continue
        seen = set()
        for log in logs:
            tx = log.get("transactionHash") or ""
            contract = (log.get("address") or "").lower()
            topics = log.get("topics") or []
            if len(topics) < 3:
                continue
            mark = (tx, contract, topics[1], topics[2])
            if mark in seen:
                continue
            seen.add(mark)
            frm = topic_addr(topics[1])
            to = topic_addr(topics[2])
            amt = hex_int(log.get("data") or "0x0") / 1e18
            if contract in QUOTE:
                usd = amt if contract != WBNB else amt * px
                if usd >= LARGE_USD:
                    side = "BUY" if to == key else "SELL"
                    ev = {
                        "chain": "bnb",
                        "wallet": addr,
                        "side": side,
                        "kind": "LARGE_TRANSFER",
                        "ca": contract,
                        "token": "WBNB" if contract == WBNB else "STABLE",
                        "tx": tx,
                        "paid": "$" + format(usd, ",.0f"),
                    }
                    print("LARGE_TRANSFER", ev["token"], addr[:10])
                    add_event(ev)
                    ada += 1
                continue
            if to == key:
                side = "BUY"
            elif frm == key:
                side = "SELL"
            else:
                continue
            ev = {
                "chain": "bnb",
                "wallet": addr,
                "side": side,
                "kind": side,
                "ca": contract,
                "token": contract[:6],
                "tx": tx,
            }
            print(side, ev["token"], addr[:10], tx[:10])
            add_event(ev)
            ada += 1
        state[key] = now_block
        time.sleep(SLEEP_WALLET)
    save_state(state)
    if ada:
        print("Flush", ada, "event")
        flush_alerts()
    else:
        print("Tidak ada event baru")


def run_loop():
    print("BNB monitor jalan. Tutup dengan Ctrl+C")
    while True:
        run_once()
        time.sleep(LOOP_SLEEP)