import requests

CHAIN_MAP = {
    "solana": "solana",
    "base": "base",
    "bnb": "bsc",
    "robinhood": "base",
}

def token_stats(chain, ca):
    chain_id = CHAIN_MAP.get((chain or "").lower(), chain)
    url = f"https://api.dexscreener.com/tokens/v1/{chain_id}/{ca}"
    out = {
        "lp_usd": None,
        "holders": None,
        "price_usd": None,
        "dex": None,
        "marketcap": None,
    }
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        pairs = data if isinstance(data, list) else data.get("pairs") or []
        if not pairs:
            return out
        pairs = sorted(
            pairs,
            key=lambda p: float(((p.get("liquidity") or {}).get("usd") or 0)),
            reverse=True,
        )
        best = pairs[0]
        info = best.get("info") or {}
        out["lp_usd"] = (best.get("liquidity") or {}).get("usd")
        out["price_usd"] = best.get("priceUsd")
        out["dex"] = best.get("dexId")
        out["marketcap"] = best.get("marketCap") or best.get("fdv")
        out["holders"] = info.get("holders") or best.get("holders")
    except Exception as e:
        print("Gagal ambil stats:", e)
    return out

def fmt_usd(n):
    if n is None:
        return "-"
    try:
        n = float(n)
    except Exception:
        return "-"
    if n >= 1000:
        return f"${n:,.0f}"
    return f"${n:,.2f}"

def usd_value(amount, price):
    try:
        return float(amount) * float(price)
    except Exception:
        return 0