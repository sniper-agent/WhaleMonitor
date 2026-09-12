import json
import os
import sys
import time
import requests

sys.path.insert(0, r"E:\WhaleMonitor\src")

from wallets import load_wallets
from signal_engine import add_event, flush_alerts

STATE_FILE = r"E:\WhaleMonitor\data\robinhood_state.json"
RPCS = [
    "https://robinhood.drpc.org",
    "https://robinhood-rpc.publicnode.com",
    "https://rpc.mainnet.chain.robinhood.com",
]
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
WETH = "0x0bd7d308f8e1639fab988df18a8011f41eacad73"
USDG = "0x5fc5360d0400a0fd4f2af552add042d716f1d168"
QUOTE = {WETH, USDG}
LARGE_USD = 10000
SLEEP_WALLET = 0.35
LOOP_SLEEP = 20
MAX_RANGE = 80

rpc_i = 0


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def rh_wallets():
    items = [w for w in load_wallets().values() if w["chain"] == "robinhood"]
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
                print("Ganti RPC", err)
                last = err
                time.sleep(1)
                continue
            return data.get("result")
        except Exception as e:
            print("Ganti RPC", str(e)[:70])
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


def eth_price():
    try:
        r = requests.get(
            "https://api.dexscreener.com/tokens/v1/robinhood/0x0bd7d308f8e1639fab988df18a8011f41eacad73",
            timeout=10,
        )
        pairs = r.json()
        if isinstance(pairs, list) and pairs:
            return float(pairs[0].get("priceUsd") or 0)
    except Exception:
        pass
    return 2500.0


def run_once():
    state = load_state()
    watched = rh_wallets()
    print("Memantau", len(watched), "wallet Robinhood")
    try:
        now_block = latest_block()
    except Exception as e:
        print("Gagal blok", e)
        return
    px = eth_price()
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
            time.sleep(0.15)
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
                usd = amt if contract == USDG else amt * px
                if usd >= LARGE_USD:
                    side = "BUY" if to == key else "SELL"
                    ev = {
                        "chain": "robinhood",
                        "wallet": addr,
                        "side": side,
                        "kind": "LARGE_TRANSFER",
                        "ca": contract,
                        "token": "USDG" if contract == USDG else "WETH",
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
                "chain": "robinhood",
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
    print("Robinhood monitor jalan. Tutup dengan Ctrl+C")
    while True:
        try:
            run_once()
        except Exception as e:
            print("Putaran gagal, lanjut", e)
        time.sleep(LOOP_SLEEP)