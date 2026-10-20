"""Conservative, rule-based Binance spot market analysis helpers.
Signals are educational estimates, not investment advice or win probabilities.
No function in this module places orders or accesses private exchange APIs.
"""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import math
import re
import time
from typing import Dict, Optional, Sequence
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import pandas as pd
import requests

SUPPORTED_SYMBOLS = ("TAO/USDT", "NEAR/USDT", "RENDER/USDT", "FET/USDT", "WLD/USDT", "SOL/USDT", "BTC/USDT", "ETH/USDT", "BNB/USDT", "DOGE/USDT", "XRP/USDT", "PEPE/USDT")
INTERVALS = ("15m", "1h", "4h")
MIN_CANDLES = 220
KLINE_LIMIT = 300
BINANCE_BASE_URLS = ("https://data-api.binance.vision", "https://api.binance.com")
RSS_FEEDS = (("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"), ("Cointelegraph", "https://cointelegraph.com/rss"), ("Decrypt", "https://decrypt.co/feed"))

class MarketDataError(RuntimeError):
    """A user-safe explanation of a market-data failure."""


def _symbol_code(symbol):
    return str(symbol).upper().replace("/", "").strip()


def _response_message(response):
    try:
        payload = response.json()
        return str(payload.get("msg") or payload.get("message") or "")[:180] if isinstance(payload, dict) else ""
    except (ValueError, AttributeError):
        return ""


def _parse_klines(payload, symbol, now):
    if not isinstance(payload, list):
        detail = str(payload.get("msg") or payload.get("message") or "")[:180] if isinstance(payload, dict) else ""
        raise MarketDataError("Malformed Binance response for {}.{}".format(symbol, " " + detail if detail else ""))
    if not payload:
        raise MarketDataError("Binance returned no candles for {}. Check symbol availability.".format(symbol))
    rows, now_ms = [], int(now.timestamp() * 1000)
    for index, row in enumerate(payload):
        if not isinstance(row, (list, tuple)) or len(row) < 7:
            raise MarketDataError("Malformed candle data for {} (row {}).".format(symbol, index + 1))
        try:
            values = [int(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]), int(row[6])]
        except (TypeError, ValueError, OverflowError):
            raise MarketDataError("Malformed numeric candle data for {} (row {}).".format(symbol, index + 1))
        if not all(math.isfinite(value) for value in values[1:6]):
            raise MarketDataError("Binance returned non-finite candle values for {}.".format(symbol))
        open_time, op, high, low, close, volume, close_time = values
        if min(op, high, low, close) <= 0 or volume < 0 or high < max(op, close) or low > min(op, close) or high < low:
            raise MarketDataError("Binance returned invalid OHLCV values for {}.".format(symbol))
        if close_time < now_ms:  # Do not analyze the still-forming candle.
            rows.append((open_time, op, high, low, close, volume, close_time))
    if len(rows) < MIN_CANDLES:
        raise MarketDataError("Insufficient completed candles for {}: received {}, need at least {} for EMA 200."
                              .format(symbol, len(rows), MIN_CANDLES))
    frame = pd.DataFrame(rows, columns=("open_time_ms", "open", "high", "low", "close", "volume", "close_time_ms"))
    frame["open_time"] = pd.to_datetime(frame["open_time_ms"], unit="ms", utc=True)
    frame["close_time"] = pd.to_datetime(frame["close_time_ms"], unit="ms", utc=True)
    return frame.drop(columns=["open_time_ms", "close_time_ms"]).reset_index(drop=True)


def fetch_klines(symbol, interval, session=requests, now=None, limit=KLINE_LIMIT):
    """Fetch validated, completed candles from public Binance endpoints."""
    code = _symbol_code(symbol)
    if interval not in INTERVALS:
        raise MarketDataError("Unsupported interval: {}. Choose 15m, 1h, or 4h.".format(interval))
    if not code or not re.fullmatch(r"[A-Z0-9]{5,20}", code):
        raise MarketDataError("Invalid Binance symbol: {}".format(symbol))
    if limit < MIN_CANDLES or limit > 1000:
        raise MarketDataError("Candle limit must be between {} and 1000.".format(MIN_CANDLES))
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=timezone.utc)
    last_error = "Network request failed."
    for base_url in BINANCE_BASE_URLS:
        for attempt in range(2):
            try:
                response = session.get(base_url + "/api/v3/klines", params={"symbol": code, "interval": interval, "limit": limit},
                                       headers={"User-Agent": "CryptoMarketDashboard/1.0"}, timeout=(4, 12))
            except requests.RequestException as exc:
                last_error = "Network error requesting Binance data: {}".format(exc.__class__.__name__)
                break
            status = getattr(response, "status_code", 0)
            if status == 429:
                header = getattr(response, "headers", {}).get("Retry-After", "1")
                try:
                    delay = min(2.0, max(0.25, float(header)))
                except (TypeError, ValueError):
                    delay = 1.0
                if attempt == 0:
                    time.sleep(delay)
                    continue
                last_error = "Binance rate limit reached (HTTP 429). Wait briefly before scanning again."
                break
            if status == 418:
                raise MarketDataError("Binance temporarily blocked requests (HTTP 418). Wait before retrying.")
            if status >= 500 or status == 0:
                last_error = "Binance market-data service returned HTTP {}.".format(status)
                break
            if status != 200:
                detail = _response_message(response)
                if status in (400, 404):
                    raise MarketDataError("{} is unavailable on Binance spot (HTTP {}). {}".format(code, status, detail).strip())
                raise MarketDataError("Binance request failed for {} (HTTP {}). {}".format(code, status, detail).strip())
            try:
                payload = response.json()
            except (ValueError, AttributeError):
                raise MarketDataError("Binance returned malformed JSON for {}.".format(code))
            return _parse_klines(payload, code, clock)
    raise MarketDataError(last_error + " Tried Binance's public market-data endpoints.")


def calculate_indicators(frame):
    required = {"high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise MarketDataError("Candle frame is missing columns: {}.".format(", ".join(sorted(missing))))
    if len(frame) < MIN_CANDLES:
        raise MarketDataError("Insufficient candles: need {} completed rows for EMA 200.".format(MIN_CANDLES))
    data = frame.copy().reset_index(drop=True)
    for name in ("high", "low", "close", "volume"):
        data[name] = pd.to_numeric(data[name], errors="coerce")
    if data[["high", "low", "close", "volume"]].isna().any().any():
        raise MarketDataError("Candle frame contains malformed numeric values.")
    close = data["close"]
    data["ema20"] = close.ewm(span=20, adjust=False, min_periods=20).mean()
    data["ema50"] = close.ewm(span=50, adjust=False, min_periods=50).mean()
    data["ema200"] = close.ewm(span=200, adjust=False, min_periods=200).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = gain / loss.replace(0, float("nan"))
    data["rsi"] = 100 - (100 / (1 + rs))
    data.loc[(loss == 0) & (gain > 0), "rsi"] = 100.0
    data.loc[(loss == 0) & (gain == 0), "rsi"] = 50.0
    ema12 = close.ewm(span=12, adjust=False, min_periods=26).mean()
    ema26 = close.ewm(span=26, adjust=False, min_periods=26).mean()
    data["macd"] = ema12 - ema26
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False, min_periods=9).mean()
    data["macd_hist"] = data["macd"] - data["macd_signal"]
    prev = close.shift(1)
    tr = pd.concat([data["high"] - data["low"], (data["high"] - prev).abs(), (data["low"] - prev).abs()], axis=1).max(axis=1)
    data["atr"] = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    data["volume_sma20"] = data["volume"].rolling(20, min_periods=20).mean()
    return data


def score_timeframe(frame):
    """Return bounded long/short feature scores for one timeframe."""
    data = calculate_indicators(frame)
    row, prev, slope = data.iloc[-1], data.iloc[-2], data.iloc[-6]
    required = ("close", "ema20", "ema50", "ema200", "rsi", "macd_hist", "atr", "volume_sma20")
    if any(pd.isna(row[key]) or not math.isfinite(float(row[key])) for key in required):
        raise MarketDataError("Indicators are not ready; more valid candles are required.")
    close, e20, e50, e200 = map(float, (row["close"], row["ema20"], row["ema50"], row["ema200"]))
    rsi, hist, prior_hist = float(row["rsi"]), float(row["macd_hist"]), float(prev["macd_hist"])
    recent, prior = data.iloc[-10:], data.iloc[-20:-10]
    high_up = recent["high"].max() > prior["high"].max()
    low_up = recent["low"].min() > prior["low"].min()
    high_down = recent["high"].max() < prior["high"].max()
    low_down = recent["low"].min() < prior["low"].min()
    volume_ok = float(row["volume"]) >= float(row["volume_sma20"]) * 1.10
    long = {"trend": 0, "ema200": 0, "rsi": 0, "macd": 0, "volume": 0, "structure": 0}
    short = {"trend": 0, "ema200": 0, "rsi": 0, "macd": 0, "volume": 0, "structure": 0}
    if close > e20 > e50 > e200 and e50 > float(slope["ema50"]) * 1.001: long["trend"] = 25
    elif close > e20 and e20 > e50: long["trend"] = 12
    if close < e20 < e50 < e200 and e50 < float(slope["ema50"]) * 0.999: short["trend"] = 25
    elif close < e20 and e20 < e50: short["trend"] = 12
    if close > e200: long["ema200"] = 10
    elif close < e200: short["ema200"] = 10
    if 50 <= rsi <= 68 and rsi > float(prev["rsi"]): long["rsi"] = 15
    elif 32 <= rsi < 50 and rsi < float(prev["rsi"]): short["rsi"] = 15
    if hist > 0: long["macd"] = 15 + (5 if hist > prior_hist else 0)
    elif hist < 0: short["macd"] = 15 + (5 if hist < prior_hist else 0)
    if volume_ok and close > e20: long["volume"] = 15
    elif volume_ok and close < e20: short["volume"] = 15
    if high_up and low_up: long["structure"] = 15
    if high_down and low_down: short["structure"] = 15
    ls, ss = min(100, max(0, sum(long.values()))), min(100, max(0, sum(short.values())))
    structure = "Higher highs and higher lows" if long["structure"] else "Lower highs and lower lows" if short["structure"] else "Mixed / unconfirmed"
    return {"long_score": ls, "short_score": ss,
            "long_confirmations": sum(v > 0 for v in long.values()), "short_confirmations": sum(v > 0 for v in short.values()),
            "long_features": long, "short_features": short, "close": close, "rsi": rsi,
            "atr": float(row["atr"]), "ema20": e20, "ema50": e50, "ema200": e200,
            "macd_hist": hist, "volume_confirmed": bool(volume_ok), "structure": structure}


def calculate_risk(entry, atr, side, capital, risk_pct, leverage, stop_atr=1.5, target1_atr=2.0, target2_atr=3.5):
    """Size a hypothetical position from planned loss and stop distance."""
    values = (entry, atr, capital, risk_pct, leverage, stop_atr, target1_atr, target2_atr)
    if not all(math.isfinite(float(x)) for x in values): raise ValueError("Risk inputs must be finite numbers.")
    if entry <= 0 or atr <= 0 or capital <= 0 or risk_pct <= 0 or leverage <= 0: raise ValueError("Entry, ATR, capital, risk percent, and leverage must be positive.")
    direction = side.upper()
    if direction not in ("LONG", "SHORT"): raise ValueError("Side must be LONG or SHORT.")
    if min(stop_atr, target1_atr, target2_atr) <= 0: raise ValueError("ATR multipliers must be positive.")
    sign, distance = (1 if direction == "LONG" else -1), atr * stop_atr
    stop, tp1, tp2 = entry - sign * distance, entry + sign * atr * target1_atr, entry + sign * atr * target2_atr
    risk_amount = capital * risk_pct / 100.0
    quantity, notional = risk_amount / distance, (risk_amount / distance) * entry
    return {"entry": entry, "stop": stop, "target1": tp1, "target2": tp2, "stop_distance": distance,
            "risk_amount": risk_amount, "quantity": quantity, "notional": notional, "margin": notional / leverage,
            "leverage": leverage, "planned_loss": quantity * distance,
            "rr_target1": abs(tp1 - entry) / distance, "rr_target2": abs(tp2 - entry) / distance}


def analyze_market(symbol, frames, capital, risk_pct, leverage, confirm_4h=False):
    required = ["15m", "1h"] + (["4h"] if confirm_4h else [])
    missing = [key for key in required if key not in frames or frames[key] is None]
    if missing: raise MarketDataError("Missing {} candle data for {}.".format(", ".join(missing), symbol))
    details = {key: score_timeframe(frames[key]) for key in required}
    weights = {"15m": 0.40, "1h": 0.60} if not confirm_4h else {"15m": 0.30, "1h": 0.45, "4h": 0.25}
    bull = sum(details[key]["long_score"] * weights[key] for key in required)
    bear = sum(details[key]["short_score"] * weights[key] for key in required)
    gap, candidate = abs(bull - bear), "LONG" if bull > bear else "SHORT" if bear > bull else None
    score, signal, reasons = max(bull, bear), "WAIT / NO TRADE", []
    if candidate:
        for interval in required:
            item, side = details[interval], candidate.lower()
            opposite = "short" if candidate == "LONG" else "long"
            side_score = item[side + "_score"]
            if side_score < (60 if interval == "4h" else 65): reasons.append("{} score is below confirmation threshold.".format(interval))
            if side_score - item[opposite + "_score"] < 10: reasons.append("{} timeframe lacks a clear directional edge.".format(interval))
            if item[side + "_confirmations"] < 3: reasons.append("{} timeframe has fewer than three confirmations.".format(interval))
        if gap < 15: reasons.append("Combined directional score difference is below 15 points.")
        for interval in ("15m", "1h"):
            rsi = details[interval]["rsi"]
            if candidate == "LONG" and rsi >= 72: reasons.append("{} RSI is extreme; avoid chasing an overbought move.".format(interval))
            if candidate == "SHORT" and rsi <= 28: reasons.append("{} RSI is extreme; avoid chasing an oversold move.".format(interval))
        if not reasons:
            signal = "BUY / LONG" if candidate == "LONG" else "SELL / SHORT"
            reasons = ["1h confirmation: " + name for name, points in details["1h"][candidate.lower() + "_features"].items() if points > 0]
    if signal == "WAIT / NO TRADE" and not reasons: reasons.append("15m and 1h do not show a meaningful directional edge.")
    risk = calculate_risk(details["1h"]["close"], details["1h"]["atr"], candidate, capital, risk_pct, leverage) if signal != "WAIT / NO TRADE" else None
    return {"symbol": symbol, "signal": signal, "score": round(min(100, max(0, score)), 1),
            "directional_gap": round(min(100, max(0, gap)), 1), "candidate": candidate or "NEUTRAL",
            "price": details["1h"]["close"], "rsi_15m": details["15m"]["rsi"], "rsi_1h": details["1h"]["rsi"],
            "rr": 2.0 / 1.5, "timeframes": details, "reasons": reasons, "risk": risk, "confirm_4h": confirm_4h}


def _local(tag): return tag.rsplit("}", 1)[-1].lower()
def _text(element): return " ".join(t.strip() for t in element.itertext() if t.strip()) if element is not None else ""
def _field(entry, name):
    for child in entry:
        if _local(child.tag) == name:
            return child.attrib.get("href", "") if name == "link" and child.attrib.get("href") else _text(child)
    return ""

def _published(value):
    if not value: return "Publication time unavailable"
    try:
        moment = parsedate_to_datetime(value)
        if moment.tzinfo is None: moment = moment.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError, OverflowError):
        try:
            moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if moment.tzinfo is None: moment = moment.replace(tzinfo=timezone.utc)
            return moment.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except (TypeError, ValueError, OverflowError): return value[:80]

def fetch_rss_news(feeds=RSS_FEEDS, session=requests, max_items=20):
    """Read public RSS/Atom feeds, deduplicate headlines, and report feed failures."""
    articles, errors, seen = [], [], set()
    for source, url in feeds:
        try:
            response = session.get(url, headers={"User-Agent": "CryptoMarketDashboard/1.0"}, timeout=(4, 10))
            if response.status_code != 200: raise ValueError("HTTP {}".format(response.status_code))
            root = ET.fromstring(response.content)
            entries = [item for item in root.iter() if _local(item.tag) in ("item", "entry")]
            if not entries: raise ValueError("feed contained no news entries")
            count = 0
            for entry in entries:
                title, link = _field(entry, "title"), _field(entry, "link")
                parsed = urlsplit(link)
                if not title or parsed.scheme not in ("http", "https") or not parsed.netloc: continue
                key = re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()
                if not key or key in seen: continue
                seen.add(key)
                date = _field(entry, "pubdate") or _field(entry, "published") or _field(entry, "updated") or _field(entry, "date")
                articles.append({"title": title[:240], "source": source, "published": _published(date), "url": link})
                count += 1
                if len(articles) >= max_items: break
            if not count: errors.append("{}: no usable articles returned.".format(source))
        except (requests.RequestException, ET.ParseError, ValueError, TypeError) as exc:
            errors.append("{}: {}".format(source, str(exc)[:140] or exc.__class__.__name__))
        if len(articles) >= max_items: break
    return {"articles": articles, "errors": errors}
