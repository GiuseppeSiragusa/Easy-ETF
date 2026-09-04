from __future__ import annotations

import asyncio
import math
import os
import statistics
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ETF World Intelligence API", version="0.5.1")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "https://giuseppesiragusa.github.io",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

TD_KEY = os.getenv("TWELVE_DATA_API_KEY", "")
AV_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
FRED_KEY = os.getenv("FRED_API_KEY", "")
CACHE_SECONDS = int(os.getenv("CACHE_SECONDS", "1800"))
CACHE: dict[str, tuple[float, Any]] = {}

# Structural ETF metadata is intentionally explicit and auditable. Market-derived fields are never faked.
ETF_UNIVERSE = {
    "VWCE": {"exchange": "XETR", "name": "Vanguard FTSE All-World UCITS ETF", "category": "Azionario globale", "quality": 94, "exposure": ["global", "usa", "europe", "asia", "technology", "financials", "industrials"]},
    "EUNL": {"exchange": "XETR", "name": "iShares Core MSCI World UCITS ETF", "category": "Mercati sviluppati", "quality": 92, "exposure": ["global", "usa", "europe", "japan", "technology", "financials"]},
    "VUAA": {"exchange": "LSE", "name": "Vanguard S&P 500 UCITS ETF", "category": "USA large cap", "quality": 91, "exposure": ["usa", "technology", "financials", "healthcare", "consumer"]},
    "EXXT": {"exchange": "XETR", "name": "iShares NASDAQ-100 UCITS ETF", "category": "Tecnologia / Growth", "quality": 87, "exposure": ["usa", "technology", "ai", "semiconductors", "growth"]},
    "EIMI": {"exchange": "LSE", "name": "iShares Core MSCI EM IMI UCITS ETF", "category": "Mercati emergenti", "quality": 82, "exposure": ["emerging", "china", "india", "asia", "technology", "commodities"]},
    "AGGH": {"exchange": "LSE", "name": "iShares Core Global Aggregate Bond UCITS ETF", "category": "Obbligazionario globale", "quality": 89, "exposure": ["bonds", "rates", "inflation", "global"]},
    "SXR8": {"exchange": "XETR", "name": "iShares Core S&P 500 UCITS ETF", "category": "USA large cap", "quality": 92, "exposure": ["usa", "technology", "financials", "healthcare", "consumer"]},
    "IUSN": {"exchange": "LSE", "name": "iShares MSCI World Small Cap UCITS ETF", "category": "Small cap globali", "quality": 85, "exposure": ["global", "usa", "europe", "industrials", "financials", "smallcap"]},
    "ZPRV": {"exchange": "XETR", "name": "SPDR MSCI USA Small Cap Value Weighted UCITS ETF", "category": "USA small cap value", "quality": 83, "exposure": ["usa", "smallcap", "financials", "industrials", "value"]},
    "ZPRX": {"exchange": "XETR", "name": "SPDR MSCI Europe Small Cap Value Weighted UCITS ETF", "category": "Europa small cap value", "quality": 82, "exposure": ["europe", "smallcap", "financials", "industrials", "value"]},
    "IITU": {"exchange": "LSE", "name": "iShares S&P 500 Information Technology Sector UCITS ETF", "category": "Tecnologia USA", "quality": 84, "exposure": ["usa", "technology", "ai", "semiconductors", "growth"]},
    "IUHC": {"exchange": "LSE", "name": "iShares S&P 500 Health Care Sector UCITS ETF", "category": "Healthcare USA", "quality": 84, "exposure": ["usa", "healthcare", "defensive"]},
    "WTAI": {"exchange": "LSE", "name": "WisdomTree Artificial Intelligence UCITS ETF", "category": "AI / Tecnologia", "quality": 78, "exposure": ["global", "technology", "ai", "semiconductors", "growth"]},
    "RBOT": {"exchange": "LSE", "name": "iShares Automation & Robotics UCITS ETF", "category": "Robotica / Automazione", "quality": 79, "exposure": ["global", "technology", "ai", "industrials", "semiconductors"]},
    "INRG": {"exchange": "LSE", "name": "iShares Global Clean Energy Transition UCITS ETF", "category": "Energia pulita", "quality": 73, "exposure": ["global", "energy", "industrials", "growth"]},
    "SGLN": {"exchange": "LSE", "name": "iShares Physical Gold ETC", "category": "Oro", "quality": 86, "exposure": ["gold", "commodities", "inflation", "rates", "geopolitics"]},
}
DEFAULT_WATCHLIST = ["VWCE", "EUNL", "VUAA", "EXXT", "EIMI", "AGGH"]
SCANNER_CURATED = list(ETF_UNIVERSE.keys())

THEMES = {
    "rates": ["rate", "rates", "interest", "yield", "treasury", "fed", "ecb", "central bank", "tassi", "rendimenti"],
    "inflation": ["inflation", "cpi", "prices", "inflazione", "prezzi"],
    "technology": ["technology", "tech", "software", "cloud", "tecnologia"],
    "ai": ["artificial intelligence", " ai ", "ai demand", "intelligenza artificiale"],
    "semiconductors": ["semiconductor", "chip", "nvidia", "tsmc", "semiconduttori"],
    "energy": ["oil", "gas", "energy", "opec", "petrolio", "energia"],
    "china": ["china", "chinese", "beijing", "cina"],
    "europe": ["europe", "eurozone", "european", "eu ", "europa"],
    "usa": ["united states", "u.s.", "us economy", "america", "usa"],
    "geopolitics": ["war", "conflict", "sanction", "missile", "attack", "geopolit", "guerra", "sanzion"],
    "trade": ["tariff", "trade", "export control", "shipping", "supply chain", "dazi", "commercio"],
    "bonds": ["bond", "fixed income", "credit", "obbligaz"],
    "growth": ["growth stocks", "growth shares", "high valuation"],
    "emerging": ["emerging market", "developing economies", "mercati emergenti"],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def cached(key: str):
    item = CACHE.get(key)
    if item and time.time() - item[0] < CACHE_SECONDS:
        return item[1]
    return None


def put_cache(key: str, value: Any):
    CACHE[key] = (time.time(), value)
    return value


def _num(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


async def get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=18) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and (data.get("status") == "error" or data.get("Error Message")):
            raise HTTPException(502, data.get("message") or data.get("Error Message") or "Provider error")
        return data


async def td_quote(symbol: str, exchange: str | None = None) -> dict[str, Any]:
    if not TD_KEY:
        raise HTTPException(503, "TWELVE_DATA_API_KEY non configurata")
    params: dict[str, Any] = {"symbol": symbol, "apikey": TD_KEY}
    if exchange:
        params["exchange"] = exchange
    data = await get_json("https://api.twelvedata.com/quote", params)
    return {
        "provider": "Twelve Data",
        "symbol": data.get("symbol", symbol),
        "exchange": data.get("exchange", exchange),
        "currency": data.get("currency"),
        "price": _num(data.get("close")),
        "change": _num(data.get("change")),
        "percent_change": _num(data.get("percent_change")),
        "previous_close": _num(data.get("previous_close")),
        "timestamp": data.get("datetime") or now_iso(),
    }


async def td_history(symbol: str, exchange: str | None = None, outputsize: int = 260) -> dict[str, Any]:
    if not TD_KEY:
        raise HTTPException(503, "TWELVE_DATA_API_KEY non configurata")
    params: dict[str, Any] = {"symbol": symbol, "interval": "1day", "outputsize": outputsize, "apikey": TD_KEY, "order": "ASC"}
    if exchange:
        params["exchange"] = exchange
    data = await get_json("https://api.twelvedata.com/time_series", params)
    values = data.get("values") or []
    closes = [_num(v.get("close")) for v in values]
    closes = [x for x in closes if x is not None]
    return {"provider": "Twelve Data", "values": values, "closes": closes, "meta": data.get("meta", {})}




async def td_etf_directory() -> list[dict[str, Any]]:
    """Reference directory. Used for discovery only; no market values are invented."""
    if not TD_KEY:
        raise HTTPException(503, "TWELVE_DATA_API_KEY non configurata")
    data = await get_json("https://api.twelvedata.com/etf", {"apikey": TD_KEY})
    rows = data.get("data") if isinstance(data, dict) else data
    return rows if isinstance(rows, list) else []


def _symbol_request(meta: dict[str, Any], symbol: str) -> str:
    ex = meta.get("exchange")
    return f"{symbol}:{ex}" if ex else symbol


async def td_batch_quote(symbols: list[str]) -> dict[str, dict[str, Any]]:
    if not TD_KEY:
        raise HTTPException(503, "TWELVE_DATA_API_KEY non configurata")
    requests = [_symbol_request(ETF_UNIVERSE.get(s, {}), s) for s in symbols]
    data = await get_json("https://api.twelvedata.com/quote", {"symbol": ",".join(requests), "apikey": TD_KEY})
    out: dict[str, dict[str, Any]] = {}
    # Twelve Data returns either a direct quote or an object keyed by requested symbol in batch mode.
    if len(symbols) == 1 and isinstance(data, dict) and "close" in data:
        data = {symbols[0]: data}
    if isinstance(data, dict):
        for symbol in symbols:
            raw = data.get(symbol) or data.get(_symbol_request(ETF_UNIVERSE.get(symbol, {}), symbol))
            if not isinstance(raw, dict):
                continue
            out[symbol] = {
                "price": _num(raw.get("close")),
                "percent_change": _num(raw.get("percent_change")),
                "currency": raw.get("currency"),
                "exchange": raw.get("exchange") or ETF_UNIVERSE.get(symbol, {}).get("exchange"),
            }
    return out


def scanner_prefilter_score(symbol: str, q: dict[str, Any] | None) -> float:
    meta = ETF_UNIVERSE.get(symbol, {})
    quality = float(meta.get("quality", 70))
    pct = float((q or {}).get("percent_change") or 0.0)
    # Mild daily weakness gets attention; very large single-day drops are penalised as risk.
    dip = max(-8.0, min(8.0, -pct * 2.0))
    if pct < -6:
        dip -= 8
    return quality * 0.7 + 30 + dip


async def av_news(limit: int = 40, topics: str = "financial_markets,economy_macro,economy_monetary,technology,energy_transportation") -> list[dict[str, Any]]:
    if not AV_KEY:
        raise HTTPException(503, "ALPHA_VANTAGE_API_KEY non configurata")
    data = await get_json("https://www.alphavantage.co/query", {"function": "NEWS_SENTIMENT", "topics": topics, "sort": "LATEST", "limit": limit, "apikey": AV_KEY})
    out = []
    for item in data.get("feed", []):
        out.append({
            "title": item.get("title") or "Notizia senza titolo",
            "summary": item.get("summary") or "",
            "source": item.get("source") or "Fonte non indicata",
            "url": item.get("url"),
            "published": item.get("time_published"),
            "sentiment_score": _num(item.get("overall_sentiment_score")) or 0.0,
            "sentiment_label": item.get("overall_sentiment_label") or "Neutral",
            "topics": item.get("topics", []),
            "ticker_sentiment": item.get("ticker_sentiment", []),
            "provider": "Alpha Vantage",
        })
    return out


def calc_metrics(closes: list[float]) -> dict[str, Any]:
    if len(closes) < 2:
        return {"drawdown_pct": None, "momentum_1m_pct": None, "momentum_3m_pct": None, "trend": "ND", "volatility_20d_pct": None}
    current = closes[-1]
    peak = max(closes)
    dd = (current / peak - 1) * 100 if peak else None

    def mom(days: int):
        if len(closes) <= days:
            return None
        base = closes[-1-days]
        return (current / base - 1) * 100 if base else None

    ma50 = sum(closes[-50:]) / min(50, len(closes))
    ma200 = sum(closes[-200:]) / min(200, len(closes))
    trend = "Positivo" if current >= ma50 >= ma200 else "Debole" if current < ma50 else "Misto"
    returns = []
    for a, b in zip(closes[-21:-1], closes[-20:]):
        if a:
            returns.append(b / a - 1)
    vol = statistics.pstdev(returns) * math.sqrt(252) * 100 if len(returns) >= 5 else None
    return {
        "drawdown_pct": round(dd, 2) if dd is not None else None,
        "momentum_1m_pct": round(mom(21), 2) if mom(21) is not None else None,
        "momentum_3m_pct": round(mom(63), 2) if mom(63) is not None else None,
        "ma50": round(ma50, 4), "ma200": round(ma200, 4), "trend": trend,
        "volatility_20d_pct": round(vol, 2) if vol is not None else None,
    }


def extract_themes(item: dict[str, Any]) -> list[str]:
    text = f" {item.get('title','')} {item.get('summary','')} ".lower()
    found = []
    for theme, terms in THEMES.items():
        if any(term in text for term in terms):
            found.append(theme)
    for t in item.get("topics", []):
        name = str(t.get("topic", "")).lower()
        if "financial" in name and "rates" not in found:
            found.append("rates")
        if "technology" in name and "technology" not in found:
            found.append("technology")
    return found


def news_impact_for_etf(items: list[dict[str, Any]], exposure: list[str]) -> dict[str, Any]:
    exp = set(exposure)
    matched = []
    weighted = []
    for item in items:
        themes = extract_themes(item)
        overlap = exp.intersection(themes)
        if not overlap:
            continue
        sentiment = max(-1.0, min(1.0, float(item.get("sentiment_score") or 0.0)))
        relevance = min(1.0, 0.35 + 0.18 * len(overlap))
        impact = sentiment * relevance
        matched.append({
            "title": item.get("title"), "source": item.get("source"), "url": item.get("url"),
            "sentiment": round(sentiment, 3), "themes": sorted(overlap), "impact": round(impact, 3),
            "published": item.get("published"),
        })
        weighted.append(impact)
    weighted = weighted[:12]
    score = sum(weighted) / len(weighted) if weighted else 0.0
    return {
        "score": round(score, 3),
        "score_0_100": int(round((score + 1) * 50)),
        "matched_count": len(matched),
        "top_news": sorted(matched, key=lambda x: abs(x["impact"]), reverse=True)[:5],
    }


def opportunity_score(metrics: dict[str, Any], news_score: float = 0.0) -> tuple[int, dict[str, float]]:
    components = {"base": 50.0, "drawdown": 0.0, "trend": 0.0, "momentum": 0.0, "news": 0.0, "volatility": 0.0}
    dd = metrics.get("drawdown_pct")
    if dd is not None:
        if -15 <= dd <= -5: components["drawdown"] = 18
        elif -25 <= dd < -15: components["drawdown"] = 8
        elif dd < -25: components["drawdown"] = -10
        elif -5 < dd <= -2: components["drawdown"] = 8
    if metrics.get("trend") == "Positivo": components["trend"] = 15
    elif metrics.get("trend") == "Debole": components["trend"] = -12
    m3 = metrics.get("momentum_3m_pct")
    if m3 is not None: components["momentum"] = max(-10, min(10, m3 / 2))
    components["news"] = max(-10, min(10, news_score * 10))
    vol = metrics.get("volatility_20d_pct")
    if vol is not None:
        if vol > 35: components["volatility"] = -8
        elif vol > 25: components["volatility"] = -4
        elif vol < 15: components["volatility"] = 3
    score = sum(components.values())
    return int(max(0, min(100, round(score)))), {k: round(v, 2) for k, v in components.items()}


def confidence_score(metrics: dict[str, Any], news_impact: dict[str, Any], quote: dict[str, Any] | None) -> tuple[int, list[str]]:
    score = 20
    reasons = []
    if quote and quote.get("price") is not None:
        score += 25; reasons.append("quotazione reale disponibile")
    filled = sum(metrics.get(k) is not None for k in ["drawdown_pct", "momentum_1m_pct", "momentum_3m_pct", "volatility_20d_pct"])
    score += filled * 8
    if metrics.get("trend") not in (None, "ND"):
        score += 8; reasons.append("storico sufficiente per il trend")
    n = news_impact.get("matched_count", 0)
    if n >= 5:
        score += 15; reasons.append("buona copertura di notizie pertinenti")
    elif n >= 2:
        score += 8; reasons.append("copertura news parziale")
    else:
        reasons.append("poche notizie direttamente pertinenti")
    return min(100, score), reasons


def classify_signal(score: int, confidence: int, metrics: dict[str, Any]) -> tuple[str, str, bool]:
    if confidence < 55:
        return "Dati insufficienti", "watch", False
    if metrics.get("trend") == "Debole" and score < 65:
        return "Attendere", "wait", False
    if score >= 78:
        return "Interessante", "good", True
    if score >= 65:
        return "Da valutare", "good", True
    if score >= 52:
        return "Da monitorare", "watch", False
    return "Attendere", "wait", False


def why_lines(metrics: dict[str, Any], news_impact: dict[str, Any], score: int) -> list[str]:
    lines = []
    dd = metrics.get("drawdown_pct")
    if dd is not None:
        if -15 <= dd <= -5: lines.append(f"Correzione del {abs(dd):.1f}% dal massimo recente, fascia spesso utile da approfondire")
        elif dd < -15: lines.append(f"Drawdown profondo del {abs(dd):.1f}%: opportunità potenziale ma rischio più alto")
        elif dd > -2: lines.append("Prezzo vicino ai massimi recenti: margine d'ingresso ridotto")
    trend = metrics.get("trend")
    if trend == "Positivo": lines.append("Trend medio-lungo ancora costruttivo")
    elif trend == "Debole": lines.append("Trend tecnico deteriorato: richiede maggiore prudenza")
    ns = news_impact.get("score", 0)
    if news_impact.get("matched_count", 0) == 0: lines.append("Copertura news specifica ancora insufficiente")
    elif ns > 0.15: lines.append("Flusso di notizie pertinente moderatamente favorevole")
    elif ns < -0.15: lines.append("Flusso di notizie pertinente ancora sfavorevole")
    else: lines.append("News pertinenti complessivamente neutrali")
    if score >= 78: lines.append("Più segnali sono coerenti, ma l'ingresso resta da frazionare")
    return lines[:4]


@app.get("/api/health")
def health():
    return {"ok": True, "version": "0.5.1", "time": now_iso(), "providers": {"twelve_data": bool(TD_KEY), "alpha_vantage": bool(AV_KEY), "fred": bool(FRED_KEY), "ecb": True}}


@app.get("/api/news")
async def news(limit: int = Query(30, ge=1, le=100)):
    key = f"news:{limit}"
    if (c := cached(key)) is not None: return c
    items = await av_news(limit=limit)
    enriched = []
    for item in items:
        themes = extract_themes(item)
        impact_strength = min(100, int(45 + 8 * len(themes) + abs(item.get("sentiment_score", 0)) * 35))
        enriched.append({**item, "themes_detected": themes, "impact_score": impact_strength})
    return put_cache(key, {"updated_at": now_iso(), "items": enriched})


async def build_intelligence(symbol: str, exchange: str | None = None, news_items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    symbol = symbol.upper()
    meta = ETF_UNIVERSE.get(symbol, {"exchange": exchange, "name": symbol, "category": "ETF", "quality": 75, "exposure": ["global"]})
    exchange = exchange or meta.get("exchange")
    q, h = await asyncio.gather(td_quote(symbol, exchange), td_history(symbol, exchange))
    metrics = calc_metrics(h["closes"])
    items = news_items or []
    ni = news_impact_for_etf(items, meta.get("exposure", []))
    opp, components = opportunity_score(metrics, ni["score"])
    conf, conf_reasons = confidence_score(metrics, ni, q)
    view, rating, buy = classify_signal(opp, conf, metrics)
    return {
        "symbol": symbol, "name": meta.get("name"), "category": meta.get("category"), "quality_score": meta.get("quality", 75),
        "opportunity_score": opp, "confidence_score": conf, "signal": view, "rating": rating, "buy_zone": buy,
        "quote": q, "metrics": metrics, "news_impact": ni, "score_components": components,
        "why": why_lines(metrics, ni, opp), "confidence_reasons": conf_reasons,
        "updated_at": now_iso(), "sources": ["Twelve Data"] + (["Alpha Vantage"] if items else []),
    }


@app.get("/api/intelligence/{symbol}")
async def intelligence(symbol: str, exchange: str | None = None):
    key = f"intel:{symbol}:{exchange}"
    if (c := cached(key)) is not None: return c
    items = []
    if AV_KEY:
        try: items = (await news(40))["items"]
        except Exception: items = []
    result = await build_intelligence(symbol, exchange, items)
    return put_cache(key, result)


@app.get("/api/dashboard")
async def dashboard():
    key = "dashboard-v4"
    if (c := cached(key)) is not None: return c
    if not TD_KEY:
        raise HTTPException(503, "Configura TWELVE_DATA_API_KEY nel backend per attivare i dati reali")
    news_items = []
    if AV_KEY:
        try: news_items = (await news(40))["items"]
        except Exception: news_items = []
    tasks = [build_intelligence(sym, ETF_UNIVERSE[sym]["exchange"], news_items) for sym in DEFAULT_WATCHLIST]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    cards = []
    for sym, r in zip(DEFAULT_WATCHLIST, results):
        if isinstance(r, Exception):
            cards.append({"symbol": sym, **ETF_UNIVERSE[sym], "error": str(r)})
        else: cards.append(r)
    valid = [x for x in cards if not x.get("error")]
    opps = [x["opportunity_score"] for x in valid]
    negative_news = sum(1 for n in news_items[:20] if (n.get("sentiment_score") or 0) < -0.15)
    risk = 50
    if opps: risk += int(max(-10, min(10, (65 - statistics.mean(opps)) / 2)))
    risk += min(15, negative_news)
    risk = max(0, min(100, risk))
    market_label = "Calmo" if risk < 40 else "Moderato" if risk < 65 else "Elevato"
    cards = sorted(cards, key=lambda x: x.get("opportunity_score", -1), reverse=True)
    return put_cache(key, {
        "updated_at": now_iso(), "market": {"risk_score": risk, "label": market_label, "summary": "Il motore combina prezzo, trend, volatilità e notizie pertinenti."},
        "etfs": cards, "news": news_items[:20],
        "providers": {"market": "Twelve Data", "news": "Alpha Vantage" if AV_KEY else None},
    })


@app.get("/api/scanner/universe")
async def scanner_universe(search: str = "", limit: int = Query(100, ge=10, le=500)):
    curated = [
        {"symbol": s, **m, "source": "curated"}
        for s, m in ETF_UNIVERSE.items()
        if not search or search.lower() in (s + " " + m.get("name", "") + " " + m.get("category", "")).lower()
    ]
    discovered: list[dict[str, Any]] = []
    if TD_KEY:
        try:
            rows = await td_etf_directory()
            for r in rows:
                name = str(r.get("name") or "")
                sym = str(r.get("symbol") or "").upper()
                text = f"{sym} {name} {r.get('exchange','')}".lower()
                if "ucits" not in text:
                    continue
                if search and search.lower() not in text:
                    continue
                if sym in ETF_UNIVERSE:
                    continue
                discovered.append({"symbol": sym, "name": name, "exchange": r.get("exchange"), "currency": r.get("currency"), "source": "Twelve Data directory"})
                if len(discovered) >= max(0, limit - len(curated)):
                    break
        except Exception:
            pass
    return {"updated_at": now_iso(), "count": min(limit, len(curated) + len(discovered)), "items": (curated + discovered)[:limit]}


@app.get("/api/scanner")
async def scanner(
    category: str = "all",
    min_quality: int = Query(70, ge=0, le=100),
    min_opportunity: int = Query(55, ge=0, le=100),
    max_results: int = Query(12, ge=3, le=20),
):
    if not TD_KEY:
        raise HTTPException(503, "Configura TWELVE_DATA_API_KEY per attivare lo scanner")
    candidates = []
    for symbol in SCANNER_CURATED:
        meta = ETF_UNIVERSE[symbol]
        if meta.get("quality", 0) < min_quality:
            continue
        if category != "all" and category.lower() not in meta.get("category", "").lower() and category.lower() not in meta.get("exposure", []):
            continue
        candidates.append(symbol)
    if not candidates:
        return {"updated_at": now_iso(), "items": [], "scanned": 0, "deep_analysed": 0}

    quotes = {}
    try:
        quotes = await td_batch_quote(candidates)
    except Exception:
        # Batch support varies by plan/provider response; deep analysis still works.
        pass
    ranked = sorted(candidates, key=lambda s: scanner_prefilter_score(s, quotes.get(s)), reverse=True)
    shortlist = ranked[:min(max_results, 12)]

    news_items = []
    if AV_KEY:
        try:
            news_items = (await news(50))["items"]
        except Exception:
            news_items = []
    sem = asyncio.Semaphore(4)
    async def one(sym: str):
        async with sem:
            try:
                return await build_intelligence(sym, ETF_UNIVERSE[sym].get("exchange"), news_items)
            except Exception as exc:
                return {"symbol": sym, **ETF_UNIVERSE[sym], "error": str(exc)}
    results = await asyncio.gather(*(one(s) for s in shortlist))
    valid = [x for x in results if not x.get("error") and x.get("opportunity_score", 0) >= min_opportunity]
    valid.sort(key=lambda x: (x.get("opportunity_score", 0), x.get("confidence_score", 0), x.get("quality_score", 0)), reverse=True)
    return {
        "updated_at": now_iso(),
        "method": "two_stage",
        "scanned": len(candidates),
        "deep_analysed": len(shortlist),
        "items": valid[:max_results],
        "note": "Ranking informativo: shortlist rapida seguita da analisi profonda su prezzo, storico, volatilità e news.",
    }


@app.get("/api/report/{symbol}")
async def report(symbol: str, exchange: str | None = None):
    data = await intelligence(symbol, exchange)
    return {
        "generated_at": now_iso(), "title": f"ETF World Intelligence Report — {data['symbol']}", "author": "Giuseppe Siragusa",
        "summary": {"signal": data["signal"], "quality_score": data["quality_score"], "opportunity_score": data["opportunity_score"], "confidence_score": data["confidence_score"]},
        "market_data": {"price": data["quote"].get("price"), "currency": data["quote"].get("currency"), **data["metrics"]},
        "reasons": data["why"], "news_impact": data["news_impact"], "score_components": data["score_components"],
        "risk_note": "Segnale informativo, non ordine di acquisto. Rivalutare dopo variazioni importanti di prezzo, trend o quadro macro/news.",
        "sources": data["sources"],
    }


@app.get("/api/macro/fred/{series_id}")
async def fred(series_id: str):
    if not FRED_KEY: raise HTTPException(503, "FRED_API_KEY non configurata")
    data = await get_json("https://api.stlouisfed.org/fred/series/observations", {"series_id": series_id, "api_key": FRED_KEY, "file_type": "json", "sort_order": "desc", "limit": 12})
    return {"provider": "FRED", "series_id": series_id, "observations": data.get("observations", []), "updated_at": now_iso()}


@app.get("/api/macro/ecb/fx/{currency}")
async def ecb_fx(currency: str):
    currency = currency.upper()
    url = f"https://data-api.ecb.europa.eu/service/data/EXR/D.{currency}.EUR.SP00.A"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url, params={"startPeriod": "2026-01-01", "format": "csvdata"}, headers={"Accept": "text/csv"})
        r.raise_for_status()
        return {"provider": "ECB", "currency": currency, "updated_at": now_iso(), "csv": r.text[-12000:]}
