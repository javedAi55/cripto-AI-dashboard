import pandas as pd
import requests
import streamlit as st

from analysis_engine import MarketDataError, SUPPORTED_SYMBOLS, analyze_market, fetch_klines, fetch_rss_news

st.set_page_config(page_title="Crypto Market Analysis", page_icon="📊", layout="wide")
st.title("📊 Crypto Market Analysis & Risk Dashboard")
st.caption("Rule-based market analysis only — scores are not win probabilities and no trades are placed.")


@st.cache_data(ttl=90, show_spinner=False)
def cached_klines(symbol, interval):
    return fetch_klines(symbol, interval)


@st.cache_data(ttl=600, show_spinner=False)
def cached_news():
    return fetch_rss_news()


def run_analysis(symbol, capital, risk_pct, leverage, confirm_4h):
    intervals = ["15m", "1h"] + (["4h"] if confirm_4h else [])
    frames = {interval: cached_klines(symbol, interval) for interval in intervals}
    return analyze_market(symbol, frames, capital, risk_pct, leverage, confirm_4h)


def format_price(value):
    return "USD " + format(value, ",.6g")


with st.sidebar:
    st.header("⚙️ Risk settings")
    capital = st.number_input("Account capital (USD)", min_value=10.0, value=500.0, step=50.0)
    risk_pct = st.slider("Maximum planned risk per trade (%)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    leverage = st.slider("Leverage used for margin estimate (not a safety rating)", min_value=1, max_value=20, value=1, step=1)
    st.caption("Leverage is only used to estimate margin. It is not safe or guaranteed.")
    confirm_4h = st.checkbox("Require 4h trend confirmation", value=False)
    st.divider()
    st.caption("Market data: public Binance spot candles. Private exchange keys are never requested.")

coin_pair = st.selectbox("🪙 Select a supported pair", SUPPORTED_SYMBOLS)
tab_analysis, tab_scanner, tab_news = st.tabs(["🎯 Single-pair analysis", "🔍 Coin scanner", "📰 Crypto news"])

with tab_analysis:
    st.write("The engine checks completed 15m and 1h candles, EMA 20/50/200, RSI, MACD, ATR, volume, and recent high/low structure. 4h confirmation is optional.")
    if st.button("Analyze selected pair", type="primary", use_container_width=True):
        try:
            with st.spinner("Fetching completed candles and evaluating confirmations…"):
                st.session_state["single_analysis"] = run_analysis(coin_pair, capital, risk_pct, leverage, confirm_4h)
                st.session_state["single_error"] = None
        except (MarketDataError, requests.RequestException, ValueError) as exc:
            st.session_state["single_analysis"] = None
            st.session_state["single_error"] = str(exc)
    if st.session_state.get("single_error"):
        st.error(st.session_state["single_error"])
    result = st.session_state.get("single_analysis")
    if result:
        st.markdown("---")
        m1, m2 = st.columns(2)
        m1.metric("Latest completed 1h close", format_price(result["price"]))
        m2.metric("Signal", result["signal"])
        m3, m4 = st.columns(2)
        m3.metric("Setup score", "{:.1f}/100".format(result["score"]))
        m4.metric("Directional score gap", "{:.1f} points".format(result["directional_gap"]))
        st.caption("A rule-based setup score is not a probability of profit. WAIT means confirmations are insufficient.")
        st.progress(result["score"] / 100.0)
        rows = []
        for interval, detail in result["timeframes"].items():
            direction = "LONG" if detail["long_score"] > detail["short_score"] else "SHORT" if detail["short_score"] > detail["long_score"] else "NEUTRAL"
            score = max(detail["long_score"], detail["short_score"])
            rows.append({"Timeframe": interval, "Close": format_price(detail["close"]),
                         "RSI (14)": round(detail["rsi"], 1), "EMA trend": direction,
                         "Directional score": "{}/100".format(score),
                         "Volume confirmed": "Yes" if detail["volume_confirmed"] else "No",
                         "Structure": detail["structure"]})
        st.subheader("Timeframe confirmations")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if result["signal"] == "WAIT / NO TRADE":
            st.warning("No trade signal. " + " ".join(result["reasons"]))
        else:
            st.success("{} — confirmations passed; this is not a guarantee.".format(result["signal"]))
            risk = result["risk"]
            c1, c2 = st.columns(2)
            c1.write("**Illustrative entry reference:** " + format_price(risk["entry"]))
            c2.write("**Stop loss:** " + format_price(risk["stop"]))
            c3, c4 = st.columns(2)
            c3.write("**Target 1:** " + format_price(risk["target1"]) + " (R:R {:.2f})".format(risk["rr_target1"]))
            c4.write("**Target 2:** " + format_price(risk["target2"]) + " (R:R {:.2f})".format(risk["rr_target2"]))
            st.subheader("Hypothetical position sizing")
            r1, r2 = st.columns(2)
            r1.metric("Quantity", "{:.6g} units".format(risk["quantity"]))
            r2.metric("Position notional", format_price(risk["notional"]))
            r3, r4 = st.columns(2)
            r3.metric("Estimated margin at {}x".format(int(risk["leverage"])), format_price(risk["margin"]))
            r4.metric("Maximum planned loss before costs", format_price(risk["planned_loss"]))
            if risk["margin"] > capital:
                st.warning("Estimated margin exceeds the selected account capital at this leverage. The risk-based position size has not been capped; review the figures before any manual decision.")
            st.caption("Position quantity uses account capital × risk % divided by stop distance. Margin is notional ÷ leverage. Fees, slippage, funding, liquidation, gaps, and exchange rules can change real outcomes; excluded from this estimate.")
            st.write("**Confirmations:** " + "; ".join(result["reasons"]))

with tab_scanner:
    st.subheader("Multi-timeframe scanner")
    st.write("Scans supported pairs using completed 15m/1h candles (and 4h when enabled). A failed symbol is reported without stopping the scan.")
    if st.button("Scan all supported pairs", use_container_width=True):
        table, errors = [], []
        progress, status = st.progress(0.0), st.empty()
        for index, symbol in enumerate(SUPPORTED_SYMBOLS):
            status.caption("Scanning {} ({}/{})".format(symbol, index + 1, len(SUPPORTED_SYMBOLS)))
            try:
                item = run_analysis(symbol, capital, risk_pct, leverage, confirm_4h)
                table.append({"Symbol": symbol, "Signal": item["signal"],
                              "Score": "{:.1f}/100".format(item["score"]),
                              "Price (1h close)": format_price(item["price"]),
                              "RSI 15m": round(item["rsi_15m"], 1), "RSI 1h": round(item["rsi_1h"], 1),
                              "Illustrative TP1 R:R": "1:{:.2f}".format(item["rr"])})
            except (MarketDataError, requests.RequestException, ValueError) as exc:
                errors.append({"Symbol": symbol, "Error": str(exc)})
            progress.progress((index + 1) / len(SUPPORTED_SYMBOLS))
        status.empty()
        st.session_state["scan_table"], st.session_state["scan_errors"] = table, errors
    if "scan_table" in st.session_state:
        if st.session_state["scan_table"]:
            st.dataframe(pd.DataFrame(st.session_state["scan_table"]), use_container_width=True, hide_index=True)
            st.caption("Illustrative target-1 R:R uses fixed ATR multiples, not historical performance. Scores are not win probabilities.")
        else:
            st.info("No symbols returned analyzable data.")
        if st.session_state["scan_errors"]:
            st.warning("Some pairs could not be scanned; successful results are still shown.")
            st.dataframe(pd.DataFrame(st.session_state["scan_errors"]), use_container_width=True, hide_index=True)

with tab_news:
    st.subheader("Public crypto news")
    st.caption("Headlines link to original publishers. No sentiment or AI classification is applied.")
    if st.button("Load / refresh news", use_container_width=True):
        cached_news.clear()
        st.session_state["news_data"] = cached_news()
    news = st.session_state.get("news_data")
    if news is None:
        st.info("Select Load / refresh news to retrieve current headlines.")
    elif news["articles"]:
        for article in news["articles"]:
            st.link_button(article["title"], article["url"], use_container_width=True)
            st.caption("{} · {}".format(article["source"], article["published"]))
    else:
        st.info("No headlines are currently available from the configured feeds.")
    if news and news["errors"]:
        with st.expander("Feed availability details"):
            for error in news["errors"]:
                st.warning(error)

st.markdown("---")
st.caption("Educational market-data tool only; not investment advice. It never places orders. Use at your own risk.")
