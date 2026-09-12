import json
import os
import time
from telegram_bot import send_telegram
from wallets import load_wallets, star_text
from token_stats import token_stats, fmt_usd

STATE_FILE = r"E:\WhaleMonitor\data\signal_state.json"
WINDOW_SEC = 10 * 60
MIN_SCORE = 3
COOLDOWN_SEC = 8 * 60

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def wallet_info(address):
    return load_wallets().get(address.lower())

def add_event(event):
    state = load_json(STATE_FILE, {"events": [], "last_alert": {}})
    event = dict(event)
    event["ts"] = time.time()
    w = wallet_info(event["wallet"])
    if not w:
        print("Wallet tidak ada di master:", event["wallet"])
        return
    event["score"] = w["score"]
    event["count"] = w["count"]
    state["events"].append(event)
    cutoff = time.time() - WINDOW_SEC
    state["events"] = [e for e in state["events"] if e["ts"] >= cutoff]
    save_json(STATE_FILE, state)

def maybe_alert(chain, ca):
    state = load_json(STATE_FILE, {"events": [], "last_alert": {}})
    now = time.time()
    cutoff = now - WINDOW_SEC
    group = [
        e for e in state["events"]
        if e["chain"] == chain and e["ca"].lower() == ca.lower() and e["ts"] >= cutoff
    ]
    if not group:
        return

    buy = 0
    sell = 0
    lines = []
    seen = set()
    token = group[-1].get("token", "")
    large = [e for e in group if e.get("kind") == "LARGE_TRANSFER"]

    for e in group:
        key = (e["wallet"].lower(), e["side"], e["tx"])
        if key in seen:
            continue
        seen.add(key)
        if e["side"] == "BUY":
            buy += e["score"]
        elif e["side"] == "SELL":
            sell += e["score"]
        kind = e.get("kind") or e["side"]
        extra = f" | {e.get('paid','')}" if e.get("kind") == "LARGE_TRANSFER" else ""
        lines.append(
            f"{kind} {star_text(e['count'])} skor {e['score']} | {e['wallet'][:8]}...{extra}"
        )

    if max(buy, sell) < MIN_SCORE and not large:
        print("Skor belum cukup:", buy, sell)
        return

    if buy > sell:
        signal = "BUY PRESSURE"
    elif sell > buy:
        signal = "SELL PRESSURE"
    elif large and buy == 0 and sell == 0:
        signal = "LARGE TRANSFER"
    else:
        signal = "NETRAL"

    last = state.get("last_alert", {}).get(ca.lower(), {})
    if (
        last.get("buy") == buy
        and last.get("sell") == sell
        and last.get("signal") == signal
        and now - last.get("ts", 0) < COOLDOWN_SEC
    ):
        print("Cooldown, tidak kirim ulang")
        return

    stats = token_stats(chain, ca)
    text = (
        "WHALE SIGNAL\n"
        f"Chain: {chain}\n"
        f"Token: ${token}\n"
        f"CA: {ca}\n"
        f"Price: {stats.get('price_usd') or '-'}\n"
        f"LP: {fmt_usd(stats.get('lp_usd'))}\n"
        f"Market cap: {fmt_usd(stats.get('marketcap'))}\n"
        f"Holders: {stats.get('holders') if stats.get('holders') is not None else '-'}\n"
        + "\n".join(lines)
        + f"\n\nBUY score : {buy}\nSELL score: {sell}\nSignal    : {signal}"
    )
    print(text)
    send_telegram(text)
    state.setdefault("last_alert", {})[ca.lower()] = {
        "ts": now,
        "buy": buy,
        "sell": sell,
        "signal": signal,
    }
    save_json(STATE_FILE, state)

def flush_alerts():
    state = load_json(STATE_FILE, {"events": [], "last_alert": {}})
    keys = {(e["chain"], e["ca"]) for e in state.get("events", [])}
    for chain, ca in keys:
        maybe_alert(chain, ca)