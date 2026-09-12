import json
import os
import time

from telegram_bot import send_telegram
from wallets import load_wallets, star_text
from token_stats import token_stats, fmt_usd

STATE_FILE = r"E:\WhaleMonitor\data\signal_state.json"
LOCK_FILE = r"E:\WhaleMonitor\data\signal_state.lock"
WINDOW_SEC = 10 * 60
MIN_SCORE = 3
COOLDOWN_SEC = 8 * 60
LOCK_WAIT = 8
LOCK_STALE = 30

SKIP_SYMBOLS = {
    "USDC", "USDT", "USD", "USDG", "USD1",
    "SOL", "WSOL", "WETH", "ETH",
    "BNB", "WBNB", "BTC", "WBTC",
    "DAI", "BUSD",
}

SKIP_CA = {
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
    "0x55d398326f99059ff775485246999027b3197955",
    "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d",
    "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "epjfwdd5aufqssqem2qn1xzybapc8g4weggkzwytdt1v",
    "es9vmfrzacermjfrf4h2fyd4kconky11mcce8benwnyb",
    "so11111111111111111111111111111111111111112",
}

CHAIN_LABEL = {
    "solana": "SOLANA",
    "robinhood": "ROBINHOOD",
    "bnb": "BNB",
    "base": "BASE",
}

def _now():
    return time.time()

def _acquire():
    start = _now()
    while True:
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            try:
                age = _now() - os.path.getmtime(LOCK_FILE)
            except OSError:
                age = LOCK_STALE + 1
            if age > LOCK_STALE:
                try:
                    os.remove(LOCK_FILE)
                    continue
                except OSError:
                    pass
            if _now() - start > LOCK_WAIT:
                return
            time.sleep(0.05)

def _release():
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw or not raw.startswith("{"):
            print("signal_state rusak. Reset.")
            return default
        data = json.loads(raw)
        if not isinstance(data, dict):
            return default
        data.setdefault("events", [])
        data.setdefault("last_alert", {})
        if not isinstance(data["events"], list):
            data["events"] = []
        if not isinstance(data["last_alert"], dict):
            data["last_alert"] = {}
        return data
    except Exception as e:
        print("signal_state rusak, di-reset:", type(e)._name_)
        return default

def save_json(path, data):
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    try:
        os.replace(tmp, path)
    except PermissionError:
        time.sleep(0.2)
        os.replace(tmp, path)

def wallet_info(address):
    return load_wallets().get((address or "").lower())

def _is_noise(event):
    token = str(event.get("token") or "").upper().lstrip("$")
    ca = str(event.get("ca") or "").lower()
    if token in SKIP_SYMBOLS:
        return True
    if ca in SKIP_CA:
        return True
    return False

def _clean_ticker(raw, stats, ca):
    for key in ("symbol", "ticker", "token"):
        val = str((stats or {}).get(key) or "").strip().lstrip("$")
        if val and not val.lower().startswith("0x") and val.upper() not in SKIP_SYMBOLS:
            return val.upper()
    raw = str(raw or "").strip().lstrip("$")
    if raw and not raw.lower().startswith("0x") and raw.upper() not in SKIP_SYMBOLS:
        return raw.upper()
    ca = str(ca or "")
    if ca.startswith("0x") and len(ca) >= 10:
        return ca[:6].upper()
    return (ca[:6] or "TOKEN").upper()

def add_event(event):
    if not isinstance(event, dict):
        print("add_event ditolak, bukan dict")
        return
    if _is_noise(event):
        print("Skip stable/noise:", event.get("token"), str(event.get("ca", ""))[:12])
        return
    _acquire()
    try:
        state = load_json(STATE_FILE, {"events": [], "last_alert": {}})
        event = dict(event)
        event["ts"] = _now()
        w = wallet_info(event.get("wallet", ""))
        if not w:
            print("Wallet tidak ada di master:", event.get("wallet"))
            return
        event["score"] = w["score"]
        event["count"] = w["count"]
        state["events"].append(event)
        cutoff = _now() - WINDOW_SEC
        state["events"] = [e for e in state["events"] if isinstance(e, dict) and e.get("ts", 0) >= cutoff]
        save_json(STATE_FILE, state)
    finally:
        _release()

def maybe_alert(chain, ca):
    state = load_json(STATE_FILE, {"events": [], "last_alert": {}})
    now = _now()
    cutoff = now - WINDOW_SEC
    ca_l = str(ca or "").lower()
    group = [
        e for e in state.get("events", [])
        if isinstance(e, dict)
        and e.get("chain") == chain
        and str(e.get("ca", "")).lower() == ca_l
        and e.get("ts", 0) >= cutoff
        and not _is_noise(e)
    ]
    if not group:
        return

    buy = 0
    sell = 0
    lines = []
    seen = set()
    large = [e for e in group if e.get("kind") == "LARGE_TRANSFER"]
    raw_token = group[-1].get("token", "")

    for e in group:
        key = (str(e.get("wallet", "")).lower(), e.get("side"))
        if key in seen:
            if e.get("side") == "BUY":
                buy += int(e.get("score") or 0)
            elif e.get("side") == "SELL":
                sell += int(e.get("score") or 0)
            continue
        seen.add(key)
        if e.get("side") == "BUY":
            buy += int(e.get("score") or 0)
        elif e.get("side") == "SELL":
            sell += int(e.get("score") or 0)
        kind = e.get("kind") or e.get("side")
        wallet = str(e.get("wallet", ""))
        short = wallet[:6] + "..." + wallet[-4:] if len(wallet) > 10 else wallet
        extra = f"  {e.get('paid')}" if e.get("kind") == "LARGE_TRANSFER" and e.get("paid") else ""
        lines.append(
            f"{kind}  {star_text(e.get('count', 1))}  skor {e.get('score')}  |  {short}{extra}"
        )

    if max(buy, sell) < MIN_SCORE and not large:
        print("Skor belum cukup:", chain, raw_token or ca_l[:10], buy, sell)
        return

    if buy > sell:
        signal = "BUY PRESSURE"
    elif sell > buy:
        signal = "SELL PRESSURE"
    elif large and buy == 0 and sell == 0:
        signal = "LARGE TRANSFER"
    else:
        signal = "NETRAL"

    last = state.get("last_alert", {}).get(ca_l, {})
    if (
        last.get("buy") == buy
        and last.get("sell") == sell
        and last.get("signal") == signal
        and last.get("chain") == chain
        and now - last.get("ts", 0) < COOLDOWN_SEC
    ):
        print("Cooldown, tidak kirim ulang")
        return

    stats = token_stats(chain, ca) or {}
    ticker = _clean_ticker(raw_token, stats, ca)
    chain_name = CHAIN_LABEL.get(chain, str(chain).upper())
    price = stats.get("price_usd") or "-"
    lp = fmt_usd(stats.get("lp_usd"))
    mc = fmt_usd(stats.get("marketcap"))
    holders = stats.get("holders")
    holders = holders if holders is not None else "-"

    text = (
        "WHALE SIGNAL\n"
        "────────────────\n"
        f"Chain     : {chain_name}\n"
        f"Token     : ${ticker}\n"
        f"CA        : {ca}\n"
        f"Price     : {price}\n"
        f"LP        : {lp}\n"
        f"Market cap: {mc}\n"
        f"Holders   : {holders}\n"
        "────────────────\n"
        + "\n".join(lines)
        + f"\n────────────────\n"
        f"BUY  {buy}   |   SELL {sell}\n"
        f"Signal : {signal}"
    )
    print(text)
    send_telegram(text)
    state.setdefault("last_alert", {})[ca_l] = {
        "ts": now,
        "buy": buy,
        "sell": sell,
        "signal": signal,
        "chain": chain,
    }
    save_json(STATE_FILE, state)

def flush_alerts(chain=None):
    if not chain:
        print("flush_alerts tanpa chain diabaikan")
        return
    _acquire()
    try:
        state = load_json(STATE_FILE, {"events": [], "last_alert": {}})
        keys = set()
        for e in state.get("events", []):
            if not isinstance(e, dict):
                continue
            if e.get("chain") != chain:
                continue
            if _is_noise(e):
                continue
            if e.get("ca"):
                keys.add((chain, e["ca"]))
        for ch, ca in keys:
            maybe_alert(ch, ca)
    finally:
        _release()