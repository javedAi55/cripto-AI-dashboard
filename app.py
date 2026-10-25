
import json
import html

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

from analysis_engine import (
    MarketDataError,
    SUPPORTED_SYMBOLS,
    analyze_market,
    calculate_indicators,
    fetch_klines,
    fetch_rss_news,
)

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="CryptoAI Pro",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# PREMIUM DARK UI
# --------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(ellipse at top left,
                rgba(15, 65, 100, .25), transparent 45%),
            #080d18;
        color: #edf3ff;
    }
    [data-testid="stSidebar"] {
        background: #0d1524;
        border-right: 1px solid #22314a;
    }
    h1, h2, h3 {
        color: #f1f6ff !important;
        letter-spacing: -.4px;
    }
    .hero {
        background: linear-gradient(120deg, #101f35, #11162b 65%, #18243a);
        border: 1px solid #2a3b56;
        border-radius: 22px;
        padding: 25px;
        margin: 8px 0 22px 0;
    }
    .hero-title {
        font-size: 30px;
        font-weight: 800;
        color: #ffffff;
    }
    .hero-sub {
        color: #a8bad4;
        margin-top: 8px;
        font-size: 14px;
    }
    .tag {
        display: inline-block;
        background: #182b40;
        border: 1px solid #304c68;
        color: #8edcff;
        padding: 5px 10px;
        border-radius: 30px;
        font-size: 12px;
        margin: 3px;
    }
    .panel {
        background: #101a2a;
        border: 1px solid #263750;
        border-radius: 17px;
        padding: 18px;
        min-height: 130px;
    }
    .panel-label {
        color: #94a8c5;
        font-size: 13px;
    }
    .panel-value {
        color: #f4f7ff;
        font-size: 23px;
        font-weight: 750;
        margin-top: 10px;
        overflow-wrap: anywhere;
    }
    .panel-note {
        color: #92a5c1;
        font-size: 12px;
        margin-top: 7px;
    }
    .bull {
        color: #35e7a1;
        text-shadow: 0 0 20px rgba(53,231,161,.3);
    }
    .bear {
        color: #ff6578;
        text-shadow: 0 0 20px rgba(255,101,120,.3);
    }
    .neutral {
        color: #f2c96d;
    }
    .creature {
        font-size: 68px;
        display: inline-block;
        animation: breathe 2.4s ease-in-out infinite;
    }
    @keyframes breathe {
        0%, 100% { transform: translateY(0) scale(1); }
        50% { transform: translateY(-7px) scale(1.035); }
    }
    div.stButton > button {
        border-radius: 11px;
        min-height: 43px;
        font-weight: 650;
        border: 1px solid #344b69;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #087e68, #159b87);
        border: none;
        color: white;
    }
    [data-testid="stMetric"] {
        background: #101a2a;
        border: 1px solid #263750;
        padding: 14px;
        border-radius: 13px;
    }
    .small-note {
        color: #91a3bc;
        font-size: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# DATA HELPERS
# --------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def cached_klines(symbol, interval):
    return fetch_klines(symbol, interval)


@st.cache_data(ttl=600, show_spinner=False)
def cached_news():
    return fetch_rss_news()


def run_analysis(symbol, capital, risk_pct, leverage, confirm_4h):
    intervals = ["15m", "1h"] + (["4h"] if confirm_4h else [])
    frames = {
        interval: cached_klines(symbol, interval)
        for interval in intervals
    }
    return analyze_market(
        symbol, frames, capital, risk_pct, leverage, confirm_4h
    )


def format_price(value):
    return "USDT " + format(float(value), ",.6g")


def display_signal(value):
    labels = {
        "BUY / LONG": "BUY / LONG — خرید",
        "SELL / SHORT": "SELL / SHORT — فروخت",
        "WAIT / NO TRADE": "WAIT — انتظار",
    }
    return labels.get(value, value)


def direction_info(signal):
    if signal == "BUY / LONG":
        return {
            "emoji": "🐂",
            "class": "bull",
            "title": "BULLISH BIAS",
            "message": "تجزیے میں تیزی کے شواہد سامنے آئے ہیں۔",
        }
    if signal == "SELL / SHORT":
        return {
            "emoji": "🐻",
            "class": "bear",
            "title": "BEARISH BIAS",
            "message": "تجزیے میں مندی کے شواہد سامنے آئے ہیں۔",
        }
    return {
        "emoji": "🐂 🐻",
        "class": "neutral",
        "title": "WAIT / NEUTRAL",
        "message": "واضح سمت کی تصدیق نہیں ہوئی؛ احتیاط بہتر ہے۔",
    }


def build_market_chart(frame, symbol, interval):
    data = calculate_indicators(frame).tail(180).reset_index(drop=True)

    required = {
        "open", "high", "low", "close", "open_time",
        "ema20", "ema50", "ema200",
    }
    missing = required.difference(data.columns)
    if missing:
        raise MarketDataError(
            "Missing chart columns: " + ", ".join(sorted(missing))
        )

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data["open_time"],
        open=data["open"],
        high=data["high"],
        low=data["low"],
        close=data["close"],
        name="Candles",
        increasing_line_color="#25d9a0",
        decreasing_line_color="#ff6177",
    ))

    line_colors = {
        "ema20": "#4cc9f0",
        "ema50": "#b28dff",
        "ema200": "#f5c45e",
    }

    for column, label in [
        ("ema20", "EMA 20"),
        ("ema50", "EMA 50"),
        ("ema200", "EMA 200"),
    ]:
        fig.add_trace(go.Scatter(
            x=data["open_time"],
            y=data[column],
            mode="lines",
            name=label,
            line=dict(color=line_colors[column], width=1.5),
        ))

    recent = data.tail(120).reset_index(drop=True)
    support_candidates, resistance_candidates = [], []

    for i in range(2, len(recent) - 2):
        low = float(recent.loc[i, "low"])
        high = float(recent.loc[i, "high"])
        lows = recent.loc[i - 2:i + 2, "low"].drop(index=i)
        highs = recent.loc[i - 2:i + 2, "high"].drop(index=i)

        if low <= float(lows.min()):
            support_candidates.append(low)
        if high >= float(highs.max()):
            resistance_candidates.append(high)

    current = float(data["close"].iloc[-1])
    supports = sorted(
        {x for x in support_candidates if x < current},
        reverse=True,
    )
    resistances = sorted(
        {x for x in resistance_candidates if x > current}
    )

    for level in supports[:2]:
        fig.add_hline(
            y=level, line_dash="dash", line_color="#25d9a0",
            annotation_text="Support",
        )
    for level in resistances[:2]:
        fig.add_hline(
            y=level, line_dash="dash", line_color="#ff6177",
            annotation_text="Resistance",
        )

    fig.update_layout(
        title=f"{symbol} · {interval} Market Chart",
        paper_bgcolor="#101a2a",
        plot_bgcolor="#101a2a",
        font=dict(color="#dce7f8"),
        xaxis_title="Time (UTC)",
        yaxis_title="Price (USDT)",
        xaxis_rangeslider_visible=False,
        height=570,
        margin=dict(l=12, r=12, t=55, b=12),
        legend=dict(orientation="h", y=1.03, x=0),
        hovermode="x unified",
    )
    fig.update_xaxes(
        showgrid=True, gridcolor="#1d2a3d",
        rangeslider_visible=False,
    )
    fig.update_yaxes(showgrid=True, gridcolor="#1d2a3d")
    return fig


def speak_analysis(text_to_speak):
    """Use browser speech synthesis where the browser supports it."""
    safe_text = json.dumps(str(text_to_speak), ensure_ascii=False)
    components.html(
        """
        <div style="font-family:Arial,sans-serif;color:#dce7f8;
                    background:#101a2a;padding:12px;border-radius:12px">
          <button id="speak" style="padding:10px 15px;border-radius:9px;
                    border:1px solid #34516f;background:#17334a;
                    color:#fff;font-weight:bold;cursor:pointer">
             🔊 Speak analysis
          </button>
          <button id="stop" style="padding:10px 15px;border-radius:9px;
                    border:1px solid #65404b;background:#35202a;
                    color:#fff;cursor:pointer">
             ⏹ Stop
          </button>
          <span id="status" style="margin-left:8px;font-size:12px">
            Press Speak analysis to hear the report.
          </span>
        </div>
        <script>
          const report = """ + safe_text + """;
          const status = document.getElementById("status");
          document.getElementById("speak").onclick = () => {
            if (!("speechSynthesis" in window) ||
                !("SpeechSynthesisUtterance" in window)) {
              status.textContent =
                "Speech is not supported by this browser.";
              return;
            }
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(report);
            utterance.lang = "en-US";
            utterance.rate = 0.94;
            utterance.pitch = 1.0;
            utterance.onstart = () => status.textContent = "Speaking…";
            utterance.onend = () => status.textContent = "Finished.";
            utterance.onerror = () => status.textContent =
              "Speech could not be played.";
            window.speechSynthesis.speak(utterance);
          };
          document.getElementById("stop").onclick = () => {
            if ("speechSynthesis" in window) {
              window.speechSynthesis.cancel();
            }
            status.textContent = "Speech stopped.";
          };
        </script>
        """,
        height=90,
    )


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Control Center")
    st.caption("CryptoAI Pro · Market analysis")

    capital = st.number_input(
        "Account capital (USD)",
        min_value=10.0, value=500.0, step=50.0,
    )
    risk_pct = st.slider(
        "Planned risk per trade (%)",
        min_value=0.1, max_value=5.0, value=1.0, step=0.1,
    )
    leverage = st.slider(
        "Leverage for margin estimate",
        min_value=1, max_value=20, value=1,
    )
    confirm_4h = st.checkbox(
        "Require 4h trend confirmation", value=False,
    )

    st.divider()
    st.markdown("**Market data**")
    st.caption("Public Binance spot candles")
    st.caption("No exchange keys. No orders placed.")
    st.caption("Scores are not win probabilities.")

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <div class="hero-title">⚡ CryptoAI Pro</div>
      <div class="hero-sub">
        Intelligent market analysis · Technical signals · Risk awareness
      </div>
      <div style="margin-top:14px">
        <span class="tag">LIVE DATA ON REQUEST</span>
        <span class="tag">MULTI-TIMEFRAME</span>
        <span class="tag">VOICE ASSISTANT</span>
        <span class="tag">RISK DASHBOARD</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

coin_pair = st.selectbox(
    "🪙 Select market / مارکیٹ منتخب کریں",
    SUPPORTED_SYMBOLS,
)

tab_market, tab_analysis, tab_scanner, tab_news = st.tabs([
    "🌐 Market Overview",
    "🎯 AI Analysis",
    "🔍 Coin Scanner",
    "📰 Crypto News",
])

# --------------------------------------------------
# MARKET OVERVIEW
# --------------------------------------------------
with tab_market:
    st.subheader("Market Overview / مارکیٹ کی صورتحال")
    st.caption(
        "Load market data to refresh the displayed price and chart. "
        "Automatic continuous refresh is not enabled in this version."
    )

    interval = st.selectbox(
        "Chart timeframe",
        ["15m", "1h", "4h"],
        index=1,
        key="overview_interval",
    )

    if st.button(
        "↻ Refresh market data",
        type="primary",
        use_container_width=True,
    ):
        cached_klines.clear()
        st.session_state["overview_error"] = None
        try:
            with st.spinner("Fetching public Binance market data…"):
                st.session_state["overview_frame"] = cached_klines(
                    coin_pair, interval
                )
                st.session_state["overview_symbol"] = coin_pair
                st.session_state["overview_interval_saved"] = interval
        except (
            MarketDataError, requests.RequestException, ValueError
        ) as exc:
            st.session_state["overview_error"] = str(exc)
            st.session_state["overview_frame"] = None

    overview_error = st.session_state.get("overview_error")
    if overview_error:
        st.error(overview_error)

    overview_frame = st.session_state.get("overview_frame")
    saved_symbol = st.session_state.get("overview_symbol")
    saved_interval = st.session_state.get("overview_interval_saved")

    if (
        overview_frame is not None
        and saved_symbol == coin_pair
        and saved_interval == interval
    ):
        latest = overview_frame.iloc[-1]
        previous = (
            overview_frame.iloc[-2]
            if len(overview_frame) > 1 else latest
        )
        price = float(latest["close"])
        previous_price = float(previous["close"])
        delta = (
            (price / previous_price - 1) * 100
            if previous_price else 0.0
        )

        a, b, c = st.columns(3)
        a.metric(
            "Latest completed candle close",
            format_price(price),
            f"{delta:+.3f}% vs. previous close",
        )
        b.metric("Selected pair", coin_pair)
        c.metric("Timeframe", interval)

        try:
            chart = build_market_chart(
                overview_frame, coin_pair, interval
            )
            st.plotly_chart(chart, use_container_width=True)
        except (MarketDataError, ValueError, KeyError) as exc:
            st.error(f"Chart could not be built: {exc}")

        st.caption(
            "The displayed change compares two completed candle closes; "
            "it is not a prediction of the next candle."
        )
    else:
        st.info(
            "Select a pair and press Refresh market data to load its "
            "completed candles and chart."
        )

    st.markdown("### 🐂 Bull & 🐻 Bear")
    st.write(
        "The characters below reflect the most recent analysis result "
        "available in this app. They do not independently predict prices."
    )

    last_result = st.session_state.get("single_analysis")
    last_symbol = st.session_state.get("single_symbol")
    if last_result and last_symbol == coin_pair:
        info = direction_info(last_result["signal"])
    else:
        info = direction_info("WAIT / NO TRADE")

    left, right = st.columns(2)
    with left:
        st.markdown(
            f"""
            <div class="panel" style="text-align:center">
              <div class="creature bull">🐂</div>
              <div class="panel-value bull">BULL</div>
              <div class="panel-note">Represents bullish analysis</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""
            <div class="panel" style="text-align:center">
              <div class="creature bear">🐻</div>
              <div class="panel-value bear">BEAR</div>
              <div class="panel-note">Represents bearish analysis</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="panel" style="margin-top:12px">
          <div class="panel-label">CURRENT ANALYSIS STATE</div>
          <div class="panel-value {info['class']}">
            {html.escape(info['emoji'])} &nbsp;
            {html.escape(info['title'])}
          </div>
          <div class="panel-note">{html.escape(info['message'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --------------------------------------------------
# SINGLE-PAIR ANALYSIS
# --------------------------------------------------
with tab_analysis:
    st.subheader("AI-assisted technical analysis")
    st.caption(
        "Rule-based analysis engine · completed candles · no trade execution"
    )

    if st.button(
        "🎯 Analyze selected pair",
        type="primary",
        use_container_width=True,
    ):
        try:
            with st.spinner(
                "Fetching candles and checking confirmations…"
            ):
                st.session_state["single_analysis"] = run_analysis(
                    coin_pair, capital, risk_pct, leverage, confirm_4h
                )
                st.session_state["single_symbol"] = coin_pair
                st.session_state["single_error"] = None
        except (
            MarketDataError, requests.RequestException, ValueError
        ) as exc:
            st.session_state["single_analysis"] = None
            st.session_state["single_error"] = str(exc)

    if st.session_state.get("single_error"):
        st.error(st.session_state["single_error"])

    result = st.session_state.get("single_analysis")
    result_symbol = st.session_state.get("single_symbol")

    if result and result_symbol == coin_pair:
        info = direction_info(result["signal"])

        st.markdown(
            f"""
            <div class="panel">
              <div class="panel-label">MARKET DIRECTION</div>
              <div class="panel-value {info['class']}">
                {html.escape(info['emoji'])}
                &nbsp; {html.escape(display_signal(result['signal']))}
              </div>
              <div class="panel-note">{html.escape(info['message'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Latest completed 1h close", format_price(result["price"]))
        m2.metric("Setup score", f"{result['score']:.1f}/100")
        m3.metric("Directional score gap", f"{result['directional_gap']:.1f}")

        st.progress(min(1.0, max(0.0, result["score"] / 100.0)))
        st.caption(
            "The setup score is not a probability of profit or a guarantee."
        )

        rows = []
        for timeframe, detail in result["timeframes"].items():
            direction = (
                "LONG" if detail["long_score"] > detail["short_score"]
                else "SHORT" if detail["short_score"] > detail["long_score"]
                else "NEUTRAL"
            )
            rows.append({
                "Timeframe": timeframe,
                "Close": format_price(detail["close"]),
                "RSI": round(detail["rsi"], 1),
                "EMA trend": direction,
                "Long score": detail["long_score"],
                "Short score": detail["short_score"],
                "Volume confirmed": detail["volume_confirmed"],
                "Structure": detail["structure"],
            })

        st.subheader("Timeframe confirmations")
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Why this result?")
        for reason in result["reasons"]:
            st.write("• " + reason)

        voice_lines = [
            f"Market analysis for {coin_pair}.",
            f"The current signal is {result['signal']}.",
            f"The setup score is {result['score']} out of 100.",
            f"The directional score gap is {result['directional_gap']} points.",
        ]
        for timeframe, detail in result["timeframes"].items():
            voice_lines.append(
                f"On the {timeframe} timeframe, the close is "
                f"{detail['close']:.8g}, RSI is {detail['rsi']:.1f}, "
                f"and the market structure is {detail['structure']}."
            )
        voice_lines.append("Reasons: " + " ".join(result["reasons"]))
        voice_lines.append(
            "This is educational technical analysis, not financial advice. "
            "Signals can be wrong."
        )

        st.subheader("🔊 Voice assistant")
        speak_analysis(" ".join(voice_lines))

        if result["signal"] == "WAIT / NO TRADE":
            st.warning(
                "No confirmed trade setup. Waiting is a valid result."
            )
        else:
            risk = result["risk"]
            st.subheader("Risk & hypothetical position sizing")

            r1, r2, r3 = st.columns(3)
            r1.metric("Illustrative entry", format_price(risk["entry"]))
            r2.metric("Stop loss", format_price(risk["stop"]))
            r3.metric("Planned loss before costs", format_price(risk["planned_loss"]))

            r4, r5, r6 = st.columns(3)
            r4.metric(
                "Target 1",
                format_price(risk["target1"]),
                f"R:R {risk['rr_target1']:.2f}",
            )
            r5.metric(
                "Target 2",
                format_price(risk["target2"]),
                f"R:R {risk['rr_target2']:.2f}",
            )
            r6.metric("Quantity", f"{risk['quantity']:.6g}")

            r7, r8 = st.columns(2)
            r7.metric("Position notional", format_price(risk["notional"]))
            r8.metric(
                f"Estimated margin at {risk['leverage']}x",
                format_price(risk["margin"]),
            )

            if risk["margin"] > capital:
                st.warning(
                    "Estimated margin exceeds the selected capital. "
                    "Review this hypothetical calculation carefully."
                )

            st.caption(
                "Fees, slippage, funding, liquidation, gaps, and exchange "
                "rules are not included in these estimates."
            )

# --------------------------------------------------
# COIN SCANNER
# --------------------------------------------------
with tab_scanner:
    st.subheader("Multi-timeframe coin scanner")
    st.write(
        "Scan supported pairs using completed 15m and 1h candles, "
        "with optional 4h confirmation."
    )

    if st.button(
        "🔍 Scan all supported pairs",
        use_container_width=True,
    ):
        table, errors = [], []
        progress = st.progress(0.0)
        status = st.empty()

        for index, symbol in enumerate(SUPPORTED_SYMBOLS):
            status.caption(
                f"Scanning {symbol} ({index + 1}/{len(SUPPORTED_SYMBOLS)})"
            )
            try:
                item = run_analysis(
                    symbol, capital, risk_pct, leverage, confirm_4h
                )
                table.append({
                    "Symbol": symbol,
                    "Signal": display_signal(item["signal"]),
                    "Score": f"{item['score']:.1f}/100",
                    "1h close": format_price(item["price"]),
                    "RSI 15m": round(item["rsi_15m"], 1),
                    "RSI 1h": round(item["rsi_1h"], 1),
                    "Target 1 R:R": f"1:{item['rr']:.2f}",
                })
            except (
                MarketDataError, requests.RequestException, ValueError
            ) as exc:
                errors.append({"Symbol": symbol, "Error": str(exc)})

            progress.progress((index + 1) / len(SUPPORTED_SYMBOLS))

        status.empty()
        st.session_state["scan_table"] = table
        st.session_state["scan_errors"] = errors

    if "scan_table" in st.session_state:
        table = st.session_state["scan_table"]
        errors = st.session_state.get("scan_errors", [])

        if table:
            st.dataframe(
                pd.DataFrame(table),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No pairs returned analyzable data.")

        if errors:
            st.warning(
                f"{len(errors)} pair(s) could not be scanned."
            )
            st.dataframe(
                pd.DataFrame(errors),
                use_container_width=True,
                hide_index=True,
            )

# --------------------------------------------------
# CRYPTO NEWS
# --------------------------------------------------
with tab_news:
    st.subheader("📰 Public crypto news")
    st.caption("Headlines link to their original publishers.")

    if st.button(
        "↻ Load / refresh news",
        use_container_width=True,
    ):
        try:
            cached_news.clear()
            st.session_state["news_data"] = cached_news()
            st.session_state["news_error"] = None
        except (
            MarketDataError, requests.RequestException, ValueError
        ) as exc:
            st.session_state["news_error"] = str(exc)

    if st.session_state.get("news_error"):
        st.error(st.session_state["news_error"])

    news = st.session_state.get("news_data")

    if news is None:
        st.info("Press Load / refresh news to retrieve headlines.")
    elif news["articles"]:
        for article in news["articles"]:
            st.link_button(
                article["title"],
                article["url"],
                use_container_width=True,
            )
            st.caption(
                f"{article['source']} · {article['published']}"
            )
    else:
        st.info("No headlines are currently available.")

    if news and news["errors"]:
        with st.expander("News feed availability details"):
            for error in news["errors"]:
                st.warning(error)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()
st.caption(
    "CryptoAI Pro · Educational market-data tool only. "
    "Not investment advice. No orders are placed. "
    "Market signals are estimates and may be wrong."
)


