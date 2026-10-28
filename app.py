# ============================================================
# CRYPTO AI DASHBOARD PRO+
# Live Market | Candles | Whale Activity | News | Voice AI
# Futures Metrics | Alerts | Watchlist | Paper Trading
# Public market data only. No real orders.
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import xml.etree.ElementTree as ET

from datetime import datetime, timezone
from urllib.parse import quote
from streamlit.components.v1 import html

# ----------------------- CONFIG -------------------------------

st.set_page_config(
    page_title="Crypto AI Dashboard Pro+",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE = "https://api.binance.com"
FUTURES = "https://fapi.binance.com"
TIMEOUT = 12

HEADERS = {
    "User-Agent": "CryptoAIDashboard/1.0"
}

# ----------------------- DESIGN -------------------------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(140deg, #08111f, #101b2d);
    color: #e8eef8;
}
section[data-testid="stSidebar"] {
    background: #0b1422;
}
div[data-testid="stMetric"] {
    background: #111f32;
    border: 1px solid #263950;
    padding: 14px;
    border-radius: 12px;
}
h1, h2, h3 {
    color: #e8eef8;
}
div.stButton > button {
    border-radius: 9px;
    font-weight: 600;
}
.small-note {
    color: #aabbd0;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------- HTTP ---------------------------------

def get_json(url, params=None):
    """Fetch public market data safely."""
    try:
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        st.warning(f"Data connection issue: {exc}")
        return None


def money(value):
    try:
        value = float(value)
        if abs(value) >= 1000:
            return f"${value:,.2f}"
        if abs(value) >= 1:
            return f"${value:,.4f}"
        return f"${value:,.8f}"
    except (TypeError, ValueError):
        return "N/A"


def number(value):
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def utc_time(timestamp=None):
    if timestamp is None:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return datetime.fromtimestamp(
        timestamp / 1000, timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S UTC")


# ----------------------- MARKET DATA ---------------------------

@st.cache_data(ttl=8, show_spinner=False)
def get_klines(symbol, interval, limit=300):
    raw = get_json(
        f"{BASE}/api/v3/klines",
        {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
    )

    if not raw:
        return pd.DataFrame()

    columns = [
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ]

    df = pd.DataFrame(raw, columns=columns)

    for col in [
        "open", "high", "low", "close", "volume",
        "quote_volume", "taker_buy_base", "taker_buy_quote"
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)

    df["EMA20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["EMA200"] = df["close"].ewm(span=200, adjust=False).mean()

    df["RSI"] = calculate_rsi(df["close"])
    df["VolumeMA20"] = df["volume"].rolling(20).mean()

    return df.dropna(subset=["close"])


def calculate_rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0).ewm(
        alpha=1 / period, min_periods=period, adjust=False
    ).mean()

    loss = (-delta.clip(upper=0)).ewm(
        alpha=1 / period, min_periods=period, adjust=False
    ).mean()

    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(50)


@st.cache_data(ttl=10, show_spinner=False)
def get_ticker(symbol):
    return get_json(
        f"{BASE}/api/v3/ticker/24hr",
        {"symbol": symbol}
    )


@st.cache_data(ttl=10, show_spinner=False)
def get_book(symbol):
    return get_json(
        f"{BASE}/api/v3/depth",
        {"symbol": symbol, "limit": 20}
    )


@st.cache_data(ttl=15, show_spinner=False)
def get_futures_metrics(symbol):
    """Public Futures statistics; not individual whale positions."""
    result = {}

    result["price"] = get_json(
        f"{FUTURES}/fapi/v1/premiumIndex",
        {"symbol": symbol}
    )

    result["oi"] = get_json(
        f"{FUTURES}/fapi/v1/openInterest",
        {"symbol": symbol}
    )

    result["longshort"] = get_json(
        f"{FUTURES}/futures/data/globalLongShortAccountRatio",
        {"symbol": symbol, "period": "5m", "limit": 1}
    )

    result["taker"] = get_json(
        f"{FUTURES}/futures/data/takerlongshortRatio",
        {"symbol": symbol, "period": "5m", "limit": 1}
    )

    return result


# ----------------------- TECHNICAL ANALYSIS --------------------

def technical_signal(df):
    if df.empty or len(df) < 30:
        return "INSUFFICIENT DATA", "Not enough candles for analysis."

    last = df.iloc[-1]
    previous = df.iloc[-2]

    bullish = (
        last["EMA20"] > last["EMA50"]
        and last["close"] > last["EMA20"]
    )

    bearish = (
        last["EMA20"] < last["EMA50"]
        and last["close"] < last["EMA20"]
    )

    if bullish and last["RSI"] < 70:
        state = "BULLISH BIAS"
    elif bearish and last["RSI"] > 30:
        state = "BEARISH BIAS"
    else:
        state = "MIXED / NEUTRAL"

    crossed_up = (
        previous["EMA20"] <= previous["EMA50"]
        and last["EMA20"] > last["EMA50"]
    )

    crossed_down = (
        previous["EMA20"] >= previous["EMA50"]
        and last["EMA20"] < last["EMA50"]
    )

    if crossed_up:
        signal = "BUY TECHNICAL SIGNAL"
    elif crossed_down:
        signal = "SELL TECHNICAL SIGNAL"
    else:
        signal = "NO NEW EMA CROSSOVER"

    return state, signal


def build_chart(df, symbol, show_volume=True):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df["time"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name=symbol,
    ))

    fig.add_trace(go.Scatter(
        x=df["time"], y=df["EMA20"],
        name="EMA 20", line=dict(width=1.4)
    ))

    fig.add_trace(go.Scatter(
        x=df["time"], y=df["EMA50"],
        name="EMA 50", line=dict(width=1.4)
    ))

    if len(df) >= 200:
        fig.add_trace(go.Scatter(
            x=df["time"], y=df["EMA200"],
            name="EMA 200", line=dict(width=1.4)
        ))

    cross_up = (
        (df["EMA20"] > df["EMA50"])
        & (df["EMA20"].shift(1) <= df["EMA50"].shift(1))
    )

    cross_down = (
        (df["EMA20"] < df["EMA50"])
        & (df["EMA20"].shift(1) >= df["EMA50"].shift(1))
    )

    buy_points = df[cross_up]
    sell_points = df[cross_down]

    fig.add_trace(go.Scatter(
        x=buy_points["time"],
        y=buy_points["low"],
        mode="markers+text",
        text=["BUY"] * len(buy_points),
        textposition="bottom center",
        name="EMA Bullish Cross",
        marker=dict(symbol="triangle-up", size=11),
    ))

    fig.add_trace(go.Scatter(
        x=sell_points["time"],
        y=sell_points["high"],
        mode="markers+text",
        text=["SELL"] * len(sell_points),
        textposition="top center",
        name="EMA Bearish Cross",
        marker=dict(symbol="triangle-down", size=11),
    ))

    fig.update_layout(
        title=f"{symbol} | Candlestick & Technical Signals",
        template="plotly_dark",
        height=620,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=1.02, x=0),
    )

    return fig


# ----------------------- WHALE PROXY ---------------------------

@st.cache_data(ttl=10, show_spinner=False)
def get_large_trades(symbol, minimum_usd=100000, limit=500):
    """
    Large public aggregate trades are a whale-activity proxy only.
    Trade size does not identify the trader or prove intent.
    """
    raw = get_json(
        f"{BASE}/api/v3/aggTrades",
        {"symbol": symbol, "limit": limit}
    )

    if not raw:
        return pd.DataFrame()

    df = pd.DataFrame(raw)

    df["price"] = pd.to_numeric(df["p"], errors="coerce")
    df["qty"] = pd.to_numeric(df["q"], errors="coerce")
    df["usd_value"] = df["price"] * df["qty"]
    df["time"] = pd.to_datetime(df["T"], unit="ms", utc=True)

    # "m" means the buyer was the maker.
    # Therefore, m=False means buyer was the taker.
    df["aggressor"] = np.where(
        df["m"].astype(bool),
        "SELL-AGGRESSOR PROXY",
        "BUY-AGGRESSOR PROXY"
    )

    df = df[df["usd_value"] >= minimum_usd].copy()
    df = df.sort_values("time", ascending=False)

    return df


def order_book_imbalance(book):
    if not book or "bids" not in book or "asks" not in book:
        return None

    bids = sum(float(row[0]) * float(row[1]) for row in book["bids"])
    asks = sum(float(row[0]) * float(row[1]) for row in book["asks"])

    total = bids + asks

    if total == 0:
        return None

    return {
        "bid_usd": bids,
        "ask_usd": asks,
        "imbalance_pct": 100 * (bids - asks) / total,
    }


# ----------------------- NEWS ENGINE ---------------------------

@st.cache_data(ttl=300, show_spinner=False)
def get_crypto_news():
    """
    Public RSS feed. A feed may occasionally be unavailable.
    News sentiment below is a lightweight keyword heuristic.
    """
    feeds = [
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Cointelegraph", "https://cointelegraph.com/rss"),
    ]

    articles = []

    for source, url in feeds:
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=10
            )
            response.raise_for_status()

            root = ET.fromstring(response.content)

            for item in root.findall(".//item"):
                title = item.findtext("title", default="").strip()
                link = item.findtext("link", default="").strip()
                pubdate = item.findtext("pubDate", default="").strip()
                description = item.findtext(
                    "description", default=""
                ).strip()

                if not title:
                    continue

                text = f"{title} {description}".lower()

                positive_words = [
                    "surge", "rally", "approval", "adoption",
                    "bullish", "inflow", "breakout", "growth",
                    "record high", "partnership"
                ]

                negative_words = [
                    "crash", "hack", "lawsuit", "ban",
                    "bearish", "outflow", "liquidation",
                    "fraud", "investigation", "sell-off"
                ]

                positive = sum(w in text for w in positive_words)
                negative = sum(w in text for w in negative_words)

                if positive > negative:
                    sentiment = "Potentially positive keywords"
                elif negative > positive:
                    sentiment = "Potentially negative keywords"
                else:
                    sentiment = "Mixed / unclear"

                articles.append({
                    "Source": source,
                    "Headline": title,
                    "Published": pubdate,
                    "Sentiment estimate": sentiment,
                    "URL": link,
                })

        except Exception:
            continue

    return pd.DataFrame(articles).drop_duplicates(
        subset=["Headline"]
    )


# ----------------------- SESSION STATE -------------------------

defaults = {
    "watchlist": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    "alerts": [],
    "paper_trades": [],
    "paper_balance": 10000.0,
    "language": "Urdu",
    "last_report": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ----------------------- SIDEBAR -------------------------------

st.sidebar.title("₿ Crypto AI Pro+")

st.sidebar.caption("Live public-market intelligence")

symbol = st.sidebar.selectbox(
    "Select Market",
    [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
        "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT",
        "LINKUSDT", "LTCUSDT", "TRXUSDT", "TONUSDT"
    ]
)

interval = st.sidebar.selectbox(
    "Chart Timeframe",
    ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
    index=2
)

language = st.sidebar.selectbox(
    "AI Voice Language",
    ["Urdu", "English"],
    index=0
)

st.session_state["language"] = language

st.sidebar.markdown("---")

if st.sidebar.button("🔄 Refresh Market Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown(
    """
    **Important**

    This app provides market information and educational signals.
    It does not guarantee profits and does not place real orders.
    """
)

# ----------------------- HEADER --------------------------------

st.title("₿ CRYPTO AI DASHBOARD PRO+")
st.caption(
    "Live Market Intelligence • Technical Analysis • News • "
    "Large-Trade Monitor • Voice Assistant"
)

st.write(f"**Last page refresh:** {utc_time()}")

# ----------------------- LOAD DATA ------------------------------

with st.spinner("Loading market data..."):
    df = get_klines(symbol, interval)
    ticker = get_ticker(symbol)
    book = get_book(symbol)
    futures = get_futures_metrics(symbol)

if df.empty:
    st.error(
        "Market data could not be loaded. Please check your connection "
        "and press Refresh Market Data."
    )
    st.stop()

last = df.iloc[-1]
previous = df.iloc[-2]

price = float(last["close"])
change_pct = float(ticker.get("priceChangePercent", 0)) if ticker else 0
quote_volume = float(ticker.get("quoteVolume", 0)) if ticker else 0

state, signal = technical_signal(df)

# ----------------------- TOP METRICS ----------------------------

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Market Price", money(price), f"{change_pct:.2f}% / 24h")
c2.metric("24h Quote Volume", f"${quote_volume:,.0f}")
c3.metric("RSI 14", f"{last['RSI']:.1f}")
c4.metric("EMA Trend", state)
c5.metric("Latest Signal", signal)

st.markdown("---")

# ----------------------- MAIN TABS ------------------------------

tabs = st.tabs([
    "📊 Live Chart",
    "🤖 AI Market Report",
    "🐋 Whale Monitor",
    "📈 Futures Data",
    "📰 Crypto News",
    "🔔 Alerts & Watchlist",
    "🧪 Paper Trading",
    "🧠 Risk Manager",
    "🔊 Voice Assistant",
    "☕ Relax & Smile",
])

# ================================================================
# TAB 1: LIVE CHART
# ================================================================

with tabs[0]:
    st.subheader(f"{symbol} — {interval} Chart")

    st.plotly_chart(
        build_chart(df, symbol),
        use_container_width=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Recent Candles")
        st.dataframe(
            df[[
                "time", "open", "high", "low", "close",
                "volume", "EMA20", "EMA50", "RSI"
            ]].tail(20).sort_values("time", ascending=False),
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.markdown("### Volume & Momentum")

        vol_df = df.tail(100)

        volume_fig = go.Figure()
        volume_fig.add_trace(go.Bar(
            x=vol_df["time"],
            y=vol_df["volume"],
            name="Volume"
        ))
        volume_fig.add_trace(go.Scatter(
            x=vol_df["time"],
            y=vol_df["VolumeMA20"],
            name="Volume MA20"
        ))

        volume_fig.update_layout(
            template="plotly_dark",
            height=350,
            title="Trading Volume"
        )

        st.plotly_chart(volume_fig, use_container_width=True)

        st.metric("Latest Close", money(price))
        st.metric("EMA 20", money(last["EMA20"]))
        st.metric("EMA 50", money(last["EMA50"]))
        st.metric("EMA 200", money(last["EMA200"]))

    st.info(
        "BUY/SELL markers show EMA crossover events. They are historical "
        "technical signals, not instructions or guarantees of future profit."
    )

# ================================================================
# TAB 2: AI MARKET REPORT
# ================================================================

with tabs[1]:
    st.subheader("🤖 AI Market Analyst")

    st.write(f"**Selected asset:** {symbol}")
    st.write(f"**Market condition:** {state}")
    st.write(f"**EMA signal:** {signal}")

    rsi = float(last["RSI"])

    if rsi >= 70:
        rsi_text = "RSI is high; price may be overheated."
    elif rsi <= 30:
        rsi_text = "RSI is low; selling pressure may be extended."
    else:
        rsi_text = "RSI is in a middle range."

    trend_text = (
        "Price is above EMA 20."
        if price > last["EMA20"]
        else "Price is below EMA 20."
    )

    volume_text = (
        "Volume is above its 20-candle average."
        if pd.notna(last["VolumeMA20"])
        and last["volume"] > last["VolumeMA20"]
        else "Volume is not above its 20-candle average."
    )

    report = f"""
    Crypto AI Market Report.

    Selected asset: {symbol}.
    Current price: {price:.8f} USDT.
    Twenty-four-hour change: {change_pct:.2f} percent.

    Overall technical condition: {state}.
    EMA signal: {signal}.
    {trend_text}
    {rsi_text}
    {volume_text}

    RSI value: {rsi:.1f}.
    Current candle timeframe: {interval}.

    This analysis uses technical indicators and public market data.
    It cannot confirm what a specific whale is doing.
    It is not a guarantee of future price movement.
    Always consider volatility, fees and risk before making a decision.
    """

    st.text_area(
        "AI Report",
        value=report.strip(),
        height=260
    )

    st.session_state["last_report"] = report.strip()

    if st.button("🔊 Speak Market Report"):
        # Voice playback uses the browser's available speech voices.
        safe_report = (
            report.strip()
            .replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("$", "\\$")
        )

        html(
            f"""
            <button onclick="speakReport()"
                    style="padding:10px 16px;border-radius:8px;">
                ▶ Play Report
            </button>
            <button onclick="window.speechSynthesis.cancel()"
                    style="padding:10px 16px;border-radius:8px;">
                ■ Stop
            </button>
            <script>
            const reportText = `{safe_report}`;
            function speakReport() {{
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(reportText);
                utterance.lang = "{'ur-PK' if language == 'Urdu' else 'en-US'}";
                utterance.rate = 0.92;
                window.speechSynthesis.speak(utterance);
            }}
            speakReport();
            </script>
            """,
            height=75
        )

    st.warning(
        "This is a rule-based market report, not a connected large language "
        "model. Live news is not automatically interpreted by an external AI."
    )

# ================================================================
# TAB 3: WHALE MONITOR
# ================================================================

with tabs[2]:
    st.subheader("🐋 Large-Trade / Whale Activity Monitor")

    st.caption(
        "Large public trades are only a proxy for possible large-player "
        "activity. They do not reveal the identity of the trader."
    )

    threshold = st.number_input(
        "Minimum trade value in USDT",
        min_value=1000,
        max_value=100000000,
        value=100000,
        step=10000
    )

    trades = get_large_trades(
        symbol,
        minimum_usd=float(threshold)
    )

    if trades.empty:
        st.info(
            "No trades above this threshold were found in the latest "
            "available aggregate-trade sample. Try a lower threshold."
        )
    else:
        buy_proxy = trades[
            trades["aggressor"] == "BUY-AGGRESSOR PROXY"
        ]["usd_value"].sum()

        sell_proxy = trades[
            trades["aggressor"] == "SELL-AGGRESSOR PROXY"
        ]["usd_value"].sum()

        a, b, c = st.columns(3)
        a.metric("Large Trade Count", len(trades))
        b.metric("Buyer-Taker Proxy", f"${buy_proxy:,.0f}")
        c.metric("Seller-Taker Proxy", f"${sell_proxy:,.0f}")

        st.markdown("### Latest Large Trades")

        view = trades[[
            "time", "price", "qty", "usd_value", "aggressor"
        ]].copy()

        view["price"] = view["price"].map(money)
        view["qty"] = view["qty"].map(number)
        view["usd_value"] = view["usd_value"].map(
            lambda x: f"${x:,.0f}"
        )

        st.dataframe(
            view.head(100),
            use_container_width=True,
            hide_index=True
        )

        chart_data = trades.sort_values("time")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=chart_data["time"],
            y=chart_data["usd_value"],
            name="Trade Value (USDT)"
        ))

        fig.update_layout(
            title="Large Trade Value Over Time",
            template="plotly_dark",
            height=350
        )

        st.plotly_chart(fig, use_container_width=True)

    imbalance = order_book_imbalance(book)

    st.markdown("### Order Book Balance")

    if imbalance:
        d1, d2, d3 = st.columns(3)

        d1.metric("Top Bid Notional", f"${imbalance['bid_usd']:,.0f}")
        d2.metric("Top Ask Notional", f"${imbalance['ask_usd']:,.0f}")
        d3.metric(
            "Bid/Ask Imbalance",
            f"{imbalance['imbalance_pct']:.2f}%"
        )

        st.caption(
            "A positive imbalance means the sampled bid notional is larger "
            "than the ask notional. Visible orders can change or be cancelled."
        )

    st.warning(
        "IMPORTANT: Spot trades do not tell us whether a particular whale "
        "opened a Futures Long or Short. Buyer/seller aggressor estimates "
        "must not be treated as confirmed whale positions."
    )

# ================================================================
# TAB 4: FUTURES DATA
# ================================================================

with tabs[3]:
    st.subheader("📈 Futures Market Statistics")

    st.caption(
        "These are public aggregate Futures statistics, not a list of "
        "individual traders or their private positions."
    )

    prem = futures.get("price") if futures else None
    oi = futures.get("oi") if futures else None
    ls = futures.get("longshort") if futures else None
    taker = futures.get("taker") if futures else None

    if prem:
        f1, f2, f3 = st.columns(3)

        f1.metric(
            "Mark Price",
            money(prem.get("markPrice"))
        )

        f2.metric(
            "Funding Rate",
            f"{float(prem.get('lastFundingRate', 0)) * 100:.5f}%"
        )

        f3.metric(
            "Index Price",
            money(prem.get("indexPrice"))
        )

        st.caption(
            f"Next funding time: {utc_time(prem.get('nextFundingTime', 0))}"
        )

    if oi:
        st.metric(
            "Open Interest (Contracts)",
            number(oi.get("openInterest"))
        )

    if ls and len(ls) > 0:
        row = ls[0]

        st.markdown("### Global Long/Short Account Ratio")

        l1, l2, l3 = st.columns(3)
        l1.metric("Long/Short Ratio", number(row.get("longShortRatio")))
        l2.metric("Long Account Share", f"{float(row.get('longAccount', 0))*100:.2f}%")
        l3.metric("Short Account Share", f"{float(row.get('shortAccount', 0))*100:.2f}%")

    if taker and len(taker) > 0:
        row = taker[0]

        st.markdown("### Taker Buy/Sell Ratio")

        t1, t2 = st.columns(2)
        t1.metric("Buy/Sell Ratio", number(row.get("buySellRatio")))
        t2.metric("Taker Buy Volume", number(row.get("buyVol")))

    if not any([prem, oi, ls, taker]):
        st.warning(
            "Futures data is currently unavailable. Check the connection "
            "or select another asset."
        )

    st.info(
        "A high Long/Short ratio does not guarantee price growth. "
        "Open Interest alone does not show whether the market is net bullish "
        "or bearish. Interpret these measures together with price and volume."
    )

# ================================================================
# TAB 5: CRYPTO NEWS
# ================================================================

with tabs[4]:
    st.subheader("📰 Crypto News Engine")

    st.caption(
        "Headlines come from public RSS feeds. Keyword labels are simple "
        "estimates, not verified financial sentiment analysis."
    )

    if st.button("Refresh News"):
        get_crypto_news.clear()

    news = get_crypto_news()

    if news.empty:
        st.warning(
            "News feeds could not be loaded. Please try again later."
        )
    else:
        sentiment_filter = st.selectbox(
            "Filter headlines",
            [
                "All",
                "Potentially positive keywords",
                "Potentially negative keywords",
                "Mixed / unclear"
            ]
        )

        filtered = news.copy()

        if sentiment_filter != "All":
            filtered = filtered[
                filtered["Sentiment estimate"] == sentiment_filter
            ]

        for _, article in filtered.head(40).iterrows():
            st.markdown(f"### {article['Headline']}")
            st.caption(
                f"{article['Source']} • {article['Published']} • "
                f"{article['Sentiment estimate']}"
            )

            if article["URL"].startswith(("https://", "http://")):
                st.markdown(f"[Read original report]({article['URL']})")

            st.markdown("---")

        st.info(
            "A headline can be positive while price falls, or negative while "
            "price rises. News labels are not trading signals."
        )

# ================================================================
# TAB 6: ALERTS & WATCHLIST
# ================================================================

with tabs[5]:
    st.subheader("🔔 Price Alerts")

    with st.form("new_alert_form"):
        alert_symbol = st.selectbox(
            "Alert asset",
            ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
             "XRPUSDT", "DOGEUSDT", "ADAUSDT"]
        )

        alert_price = st.number_input(
            "Alert price (USDT)",
            min_value=0.00000001,
            value=1000.0,
            format="%.8f"
        )

        direction = st.radio(
            "Trigger when price is",
            ["Above or equal", "Below or equal"],
            horizontal=True
        )

        add_alert = st.form_submit_button("Add Alert")

        if add_alert:
            st.session_state["alerts"].append({
                "symbol": alert_symbol,
                "price": float(alert_price),
                "direction": direction,
                "triggered": False,
            })
            st.success("Alert added to this session.")

    st.markdown("### Current Alerts")

    for idx, alert in enumerate(st.session_state["alerts"]):
        current_ticker = get_ticker(alert["symbol"])

        current_price = (
            float(current_ticker["lastPrice"])
            if current_ticker else None
        )

        triggered = False

        if current_price is not None:
            if alert["direction"] == "Above or equal":
                triggered = current_price >= alert["price"]
            else:
                triggered = current_price <= alert["price"]

        if triggered and not alert["triggered"]:
            alert["triggered"] = True
            st.warning(
                f"🔔 PRICE ALERT: {alert['symbol']} is now "
                f"{money(current_price)}"
            )

        status = "TRIGGERED" if alert["triggered"] else "Waiting"

        st.write(
            f"**{alert['symbol']}** — {alert['direction']} "
            f"{money(alert['price'])} | Current: {money(current_price)} "
            f"| {status}"
        )

    if st.button("Clear All Alerts"):
        st.session_state["alerts"] = []
        st.rerun()

    st.caption(
        "Alerts are checked when the app reruns. This is not a background "
        "notification service; the page must be refreshed for checks."
    )

    st.markdown("---")
    st.subheader("⭐ Watchlist")

    watch_symbol = st.selectbox(
        "Add asset to watchlist",
        ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
         "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT"]
    )

    if st.button("Add to Watchlist"):
        if watch_symbol not in st.session_state["watchlist"]:
            st.session_state["watchlist"].append(watch_symbol)

    watch_rows = []

    for watch in st.session_state["watchlist"]:
        wt = get_ticker(watch)

        if wt:
            watch_rows.append({
                "Symbol": watch,
                "Price": money(wt.get("lastPrice")),
                "24h Change": f"{float(wt.get('priceChangePercent', 0)):.2f}%",
                "24h Quote Volume": f"${float(wt.get('quoteVolume', 0)):,.0f}",
            })

    if watch_rows:
        st.dataframe(
            pd.DataFrame(watch_rows),
            use_container_width=True,
            hide_index=True
        )

    remove_symbol = st.selectbox(
        "Remove from watchlist",
        ["None"] + st.session_state["watchlist"]
    )

    if st.button("Remove Selected"):
        if remove_symbol != "None":
            st.session_state["watchlist"].remove(remove_symbol)
            st.rerun()

    st.caption(
        "Watchlist and alerts currently live in session memory. They may "
        "reset when the session restarts."
    )

# ================================================================
# TAB 7: PAPER TRADING
# ================================================================

with tabs[6]:
    st.subheader("🧪 Paper Trading — Simulation Only")

    st.metric(
        "Virtual Starting/Available Balance",
        f"${st.session_state['paper_balance']:,.2f}"
    )

    st.caption(
        "This is a simplified simulation. It does not send real orders, "
        "include exchange execution, or guarantee realistic fills."
    )

    with st.form("paper_trade_form"):
        paper_symbol = st.selectbox(
            "Asset",
            ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
             "XRPUSDT", "DOGEUSDT"]
        )

        paper_side = st.radio(
            "Simulated action",
            ["BUY", "SELL"],
            horizontal=True
        )

        paper_usd = st.number_input(
            "Notional amount (USDT)",
            min_value=10.0,
            max_value=1000000.0,
            value=100.0
        )

        submit_paper = st.form_submit_button("Place Simulated Trade")

        if submit_paper:
            pt = get_ticker(paper_symbol)

            if not pt:
                st.error("Could not fetch current price.")
            elif paper_usd > st.session_state["paper_balance"]:
                st.error("Insufficient virtual balance.")
            else:
                entry = float(pt["lastPrice"])

                st.session_state["paper_trades"].append({
                    "time": utc_time(),
                    "symbol": paper_symbol,
                    "side": paper_side,
                    "notional": float(paper_usd),
                    "entry": entry,
                })

                # Simplified accounting: reserve the notional.
                st.session_state["paper_balance"] -= float(paper_usd)

                st.success(
                    f"Simulated {paper_side} recorded at {money(entry)}."
                )

    st.markdown("### Simulated Trade History")

    if st.session_state["paper_trades"]:
        paper_df = pd.DataFrame(st.session_state["paper_trades"])
        st.dataframe(
            paper_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No simulated trades yet.")

    if st.button("Reset Paper Trading"):
        st.session_state["paper_trades"] = []
        st.session_state["paper_balance"] = 10000.0
        st.rerun()

# ================================================================
# TAB 8: RISK MANAGER
# ================================================================

with tabs[7]:
    st.subheader("🧠 Position Size & Risk Calculator")

    account = st.number_input(
        "Account equity (USDT)",
        min_value=1.0,
        value=1000.0
    )

    risk_pct = st.slider(
        "Risk per trade (%)",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1
    )

    entry_price = st.number_input(
        "Entry price",
        min_value=0.00000001,
        value=float(price),
        format="%.8f"
    )

    stop_price = st.number_input(
        "Stop-loss price",
        min_value=0.00000001,
        value=float(price * 0.98),
        format="%.8f"
    )

    target_price = st.number_input(
        "Take-profit price",
        min_value=0.00000001,
        value=float(price * 1.04),
        format="%.8f"
    )

    if entry_price > 0 and stop_price > 0:
        distance = abs(entry_price - stop_price)

        if distance == 0:
            st.error("Entry and stop-loss cannot be the same.")
        else:
            risk_amount = account * risk_pct / 100
            quantity = risk_amount / distance
            notional = quantity * entry_price

            reward_distance = abs(target_price - entry_price)
            reward = quantity * reward_distance
            rr = reward / risk_amount if risk_amount > 0 else 0

            r1, r2, r3 = st.columns(3)

            r1.metric("Maximum Planned Risk", f"${risk_amount:,.2f}")
            r2.metric("Estimated Position Size", f"{quantity:.6f}")
            r3.metric("Notional Exposure", f"${notional:,.2f}")

            st.metric("Potential Reward/Risk", f"{rr:.2f} : 1")

            st.caption(
                "This calculation excludes fees, slippage, funding, gaps "
                "and liquidation. A stop-loss cannot guarantee the exact "
                "exit price."
            )

# ================================================================
# TAB 9: VOICE ASSISTANT
# ================================================================

with tabs[8]:
    st.subheader("🔊 AI Voice Assistant")

    st.write(
        "Use this assistant to listen to the latest rule-based market report."
    )

    if st.session_state["last_report"]:
        st.text_area(
            "Latest Report",
            value=st.session_state["last_report"],
            height=200,
            key="voice_report_display"
        )

        report_text = st.session_state["last_report"]

        if st.button("▶ Speak Latest Report"):
            # Streamlit browser component speaks using the local browser.
            # Browser language support varies by device.
            import json
            encoded = json.dumps(report_text)

            html(
                f"""
                <button onclick="speak()"
                        style="padding:10px;border-radius:8px;">
                    ▶ Speak
                </button>
                <button onclick="window.speechSynthesis.cancel()"
                        style="padding:10px;border-radius:8px;">
                    ■ Stop
                </button>
                <script>
                function speak() {{
                    window.speechSynthesis.cancel();
                    const u = new SpeechSynthesisUtterance({encoded});
                    u.lang = "{'ur-PK' if language == 'Urdu' else 'en-US'}";
                    u.rate = 0.9;
                    window.speechSynthesis.speak(u);
                }}
                speak();
                </script>
                """,
                height=70
            )
    else:
        st.info(
            "Open AI Market Report and generate the market report first."
        )

    st.caption(
        "This uses the browser's built-in voice system, not a dedicated "
        "cloud AI voice. Urdu voice availability depends on the device."
    )

# ================================================================
# TAB 10: RELAX & SMILE
# ================================================================

with tabs[9]:
    st.subheader("☕ Relax & Smile — AI Brother Break Room")

    st.write(
        "Markets can be stressful. A short break may help you think clearly."
    )

    jokes = [
        "Why did the crypto trader bring a ladder? Because the market said "
        "'we are going to the moon!'",
        "My chart said 'be patient'. So I stared at it for six hours.",
        "A candle told me it was bullish. Then the next candle said, "
        "'let's discuss this later.'",
        "Remember: the market doesn't know your entry price. Be kind to "
        "yourself and manage your risk."
    ]

    if st.button("😄 Give Me a Crypto Smile"):
        st.info(np.random.choice(jokes))

    st.markdown("### 🫁 One-Minute Breathing Break")

    st.write(
        "Relax your shoulders. Breathe in gently for 4 seconds, "
        "then breathe out slowly for 6 seconds. Repeat comfortably. "
        "Stop if you feel dizzy."
    )

    if st.button("Start Breathing Exercise"):
        html(
            """
            <div style="font-size:20px;text-align:center;padding:20px;">
                <div id="breath" style="font-weight:bold;">Get comfortable</div>
                <div id="count" style="font-size:38px;">Ready</div>
                <script>
                let phase = 0;
                let remaining = 4;
                const labels = ["Breathe in gently", "Breathe out slowly"];
                const durations = [4, 6];

                function tick() {
                    document.getElementById("breath").innerText = labels[phase];
                    document.getElementById("count").innerText = remaining;

                    remaining--;

                    if (remaining < 0) {
                        phase = 1 - phase;
                        remaining = durations[phase];
                    }
                }

                tick();
                setInterval(tick, 1000);
                </script>
            </div>
            """,
            height=150
        )

    st.markdown("---")
    st.success(
        "A friendly reminder: you do not need to catch every move. "
        "Protecting your capital and your peace of mind matters too."
    )

# ----------------------- FOOTER --------------------------------

st.markdown("---")

st.caption(
    "Crypto AI Dashboard Pro+ | Public market data | "
    "Educational information only | No real orders are sent."
)

st.caption(
    "Data availability, freshness and API limits depend on the providers. "
    "Indicators, news labels and large-trade classifications may be wrong."
)
