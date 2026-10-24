import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
from analysis_engine import (
    MarketDataError,
    SUPPORTED_SYMBOLS,
    analyze_market,
    calculate_indicators,
    fetch_klines,
    fetch_rss_news,
)

st.set_page_config(page_title="Crypto Market Analysis", page_icon="📊", layout="wide")
st.title("📊 Crypto Market Analysis & Risk Dashboard / کرپٹو مارکیٹ تجزیہ اور رسک ڈیش بورڈ")
st.caption("Rule-based market analysis only — scores are not win probabilities and no trades are placed. / یہ اصولوں پر مبنی تجزیہ ہے؛ اسکور جیتنے کا امکان نہیں اور کوئی ٹریڈ نہیں لگائی جاتی۔")


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

def build_market_chart(frame, symbol):
    """Build a candlestick chart with EMA and simple support/resistance levels."""
    data = calculate_indicators(frame).copy()

    if "open" not in data.columns:
        raise MarketDataError("Candle data is missing the open price.")

    if "open_time" not in data.columns:
        raise MarketDataError("Candle data is missing candle timestamps.")

    data = data.tail(180).reset_index(drop=True)

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data["open_time"],
        open=data["open"],
        high=data["high"],
        low=data["low"],
        close=data["close"],
        name="Candlesticks",
    ))

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
        ))

    # Find recent local highs and lows to estimate horizontal levels.
    recent = data.tail(120).reset_index(drop=True)
    support_candidates = []
    resistance_candidates = []

    for i in range(2, len(recent) - 2):
        low = float(recent.loc[i, "low"])
        high = float(recent.loc[i, "high"])

        nearby_lows = recent.loc[i - 2:i + 2, "low"].drop(index=i)
        nearby_highs = recent.loc[i - 2:i + 2, "high"].drop(index=i)

        if low <= float(nearby_lows.min()):
            support_candidates.append(low)

        if high >= float(nearby_highs.max()):
            resistance_candidates.append(high)

    current_price = float(data["close"].iloc[-1])

    supports = sorted(
        [level for level in support_candidates if level < current_price],
        reverse=True,
    )
    resistances = sorted(
        [level for level in resistance_candidates if level > current_price]
    )

    # Draw up to two nearby levels on each side of the current price.
    for level in supports[:2]:
        fig.add_hline(
            y=level,
            line_dash="dash",
            annotation_text="Support",
        )

    for level in resistances[:2]:
        fig.add_hline(
            y=level,
            line_dash="dash",
            annotation_text="Resistance",
        )

    fig.update_layout(
        title="{} — 1h Market Chart".format(symbol),
        xaxis_title="Time (UTC)",
        yaxis_title="Price (USDT)",
        xaxis_rangeslider_visible=False,
        height=650,
        legend_title="Indicators",
        margin=dict(l=10, r=10, t=55, b=10),
    )

    return fig


def display_signal(value):
    return {"BUY / LONG": "BUY / LONG — خرید / لانگ", "SELL / SHORT": "SELL / SHORT — فروخت / شارٹ", "WAIT / NO TRADE": "WAIT / NO TRADE — انتظار / ٹریڈ نہیں"}.get(value, value)


with st.sidebar:
    st.header("⚙️ Risk settings / رسک سیٹنگز")
    capital = st.number_input("Account capital (USD) / کل سرمایہ (USD)", min_value=10.0, value=500.0, step=50.0)
    risk_pct = st.slider("Maximum planned risk per trade (%) / فی ٹریڈ زیادہ سے زیادہ رسک (%)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    leverage = st.slider("Leverage used for margin estimate (not a safety rating) / مارجن کا اندازہ لگانے کے لیے لیوریج (حفاظت کی ضمانت نہیں)", min_value=1, max_value=20, value=1, step=1)
    st.caption("Leverage is only used to estimate margin. It is not safe or guaranteed. / لیوریج صرف مارجن کے اندازے کے لیے ہے؛ یہ محفوظ یا یقینی نہیں۔")
    confirm_4h = st.checkbox("Require 4h trend confirmation / 4 گھنٹے کے ٹرینڈ کی تصدیق لازم کریں", value=False)
    st.divider()
    st.caption("Market data: public Binance spot candles. Private exchange keys are never requested. / ڈیٹا Binance کی عوامی اسپاٹ کینڈلز سے ہے؛ نجی ایکسچینج کیز نہیں مانگی جاتیں۔")

coin_pair = st.selectbox("🪙 Select a supported pair / دستیاب کوائن منتخب کریں", SUPPORTED_SYMBOLS)
tab_analysis, tab_scanner, tab_news = st.tabs(["🎯 Single-pair analysis / انفرادی تجزیہ", "🔍 Coin scanner / کوائن اسکینر", "📰 Crypto news / کرپٹو خبریں"])

with tab_analysis:
   
    st.subheader("📈 Interactive Market Chart / انٹرایکٹو مارکیٹ چارٹ")

    if st.button(
        "Load 1h chart / ایک گھنٹے کا چارٹ دکھائیں",
        use_container_width=True,
    ):
        try:
            with st.spinner("Loading completed candles... / مکمل کینڈلز لوڈ ہو رہی ہیں..."):
                st.session_state["chart_frame"] = cached_klines(
                    coin_pair, "1h"
                )
                st.session_state["chart_error"] = None
        except (MarketDataError, requests.RequestException, ValueError) as exc:
            st.session_state["chart_frame"] = None
            st.session_state["chart_error"] = str(exc)

    if st.session_state.get("chart_error"):
        st.error(st.session_state["chart_error"])

    chart_frame = st.session_state.get("chart_frame")

    if chart_frame is not None:
        try:
            fig = build_market_chart(chart_frame, coin_pair)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "EMA lines and nearby support/resistance are technical "
                "references, not guaranteed predictions. / "
                "یہ تکنیکی اشارے ہیں، مستقبل کی ضمانت نہیں۔"
            )
        except (MarketDataError, ValueError, KeyError) as exc:
            st.error("Could not build chart: {}".format(exc))
 st.write("The engine checks completed 15m and 1h candles, EMA 20/50/200, RSI, MACD, ATR, volume, and recent high/low structure. 4h confirmation is optional. / مکمل 15m اور 1h کینڈلز، EMA 20/50/200، RSI، MACD، ATR، والیوم اور قیمت کا ڈھانچہ دیکھا جاتا ہے؛ 4h تصدیق اختیاری ہے۔")
    if st.button("Analyze selected pair / منتخب کوائن کا تجزیہ کریں", type="primary", use_container_width=True):
        try:
            with st.spinner("Fetching completed candles and evaluating confirmations… / مکمل کینڈلز اور تصدیقات دیکھی جا رہی ہیں…"):
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
        m1.metric("Latest completed 1h close / تازہ مکمل 1h کلوز", format_price(result["price"]))
        m2.metric("Signal / اشارہ", display_signal(result["signal"]))
        m3, m4 = st.columns(2)
        m3.metric("Setup score / سیٹ اپ اسکور", "{:.1f}/100".format(result["score"]))
        m4.metric("Directional score gap / سمت کے اسکور کا فرق", "{:.1f} points".format(result["directional_gap"]))
        st.caption("A rule-based setup score is not a probability of profit. WAIT means confirmations are insufficient. / یہ اسکور منافع کا امکان نہیں؛ WAIT کا مطلب تصدیق ناکافی ہے۔")
        st.progress(result["score"] / 100.0)
        rows = []
        for interval, detail in result["timeframes"].items():
            direction = "LONG" if detail["long_score"] > detail["short_score"] else "SHORT" if detail["short_score"] > detail["long_score"] else "NEUTRAL"
            score = max(detail["long_score"], detail["short_score"])
            rows.append({"Timeframe / ٹائم فریم": interval, "Close / کلوز": format_price(detail["close"]),
                         "RSI (14)": round(detail["rsi"], 1), "EMA trend / رجحان": direction,
                         "Directional score / سمتی اسکور": "{}/100".format(score),
                         "Volume confirmed / والیوم تصدیق": "Yes / ہاں" if detail["volume_confirmed"] else "No / نہیں",
                         "Structure / قیمت کا ڈھانچہ": detail["structure"]})
        st.subheader("Timeframe confirmations / ٹائم فریم کی تصدیق")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if result["signal"] == "WAIT / NO TRADE":
            st.warning("No trade signal / کوئی ٹریڈ سگنل نہیں۔ " + " ".join(result["reasons"]))
        else:
            st.success("{} — confirmations passed; this is not a guarantee. / تصدیقات پوری ہوئیں، مگر نتیجے کی ضمانت نہیں۔".format(display_signal(result["signal"])))
            risk = result["risk"]
            c1, c2 = st.columns(2)
            c1.write("**Illustrative entry reference / اندازاً انٹری:** " + format_price(risk["entry"]))
            c2.write("**Stop loss / اسٹاپ لاس:** " + format_price(risk["stop"]))
            c3, c4 = st.columns(2)
            c3.write("**Target 1 / ہدف 1:** " + format_price(risk["target1"]) + " (R:R {:.2f})".format(risk["rr_target1"]))
            c4.write("**Target 2 / ہدف 2:** " + format_price(risk["target2"]) + " (R:R {:.2f})".format(risk["rr_target2"]))
            st.subheader("Hypothetical position sizing / فرضی پوزیشن سائزنگ")
            r1, r2 = st.columns(2)
            r1.metric("Quantity / مقدار", "{:.6g} units".format(risk["quantity"]))
            r2.metric("Position notional / پوزیشن کی کل مالیت", format_price(risk["notional"]))
            r3, r4 = st.columns(2)
            r3.metric("Estimated margin at {}x / اندازاً مارجن".format(int(risk["leverage"])), format_price(risk["margin"]))
            r4.metric("Maximum planned loss before costs / اخراجات سے پہلے زیادہ سے زیادہ طے شدہ نقصان", format_price(risk["planned_loss"]))
            if risk["margin"] > capital:
                st.warning("Estimated margin exceeds the selected account capital at this leverage. The risk-based position size has not been capped; review before any manual decision. / اندازاً مارجن منتخب سرمائے سے زیادہ ہے؛ رسک کے مطابق پوزیشن سائز کم نہیں کیا گیا، دستی فیصلہ کرنے سے پہلے اعداد دیکھیں۔")
            st.caption("Position quantity uses account capital × risk % divided by stop distance. Margin is notional ÷ leverage. Fees, slippage, funding, liquidation, gaps, and exchange rules can change real outcomes; excluded from this estimate. / مقدار = سرمایہ × رسک فیصد ÷ اسٹاپ فاصلہ؛ فیس، سلپیج، فنڈنگ، لیکویڈیشن اور ایکسچینج قواعد شامل نہیں۔")
            st.write("**Confirmations / تصدیقات:** " + "; ".join(result["reasons"]))

with tab_scanner:
    st.subheader("Multi-timeframe scanner / ملٹی ٹائم فریم اسکینر")
    st.write("Scans supported pairs using completed 15m/1h candles (and 4h when enabled). A failed symbol is reported without stopping the scan. / مکمل 15m/1h کینڈلز (اور انتخاب پر 4h) سے دستیاب کوائنز اسکین کرتا ہے؛ ناکام کوائن کی رپورٹ الگ آتی ہے۔")
    if st.button("Scan all supported pairs / تمام دستیاب کوائن اسکین کریں", use_container_width=True):
        table, errors = [], []
        progress, status = st.progress(0.0), st.empty()
        for index, symbol in enumerate(SUPPORTED_SYMBOLS):
            status.caption("Scanning / اسکین {} ({}/{})".format(symbol, index + 1, len(SUPPORTED_SYMBOLS)))
            try:
                item = run_analysis(symbol, capital, risk_pct, leverage, confirm_4h)
                table.append({"Symbol / کوائن": symbol, "Signal / اشارہ": display_signal(item["signal"]),
                              "Score / اسکور": "{:.1f}/100".format(item["score"]),
                              "Price (1h close) / قیمت": format_price(item["price"]),
                              "RSI 15m": round(item["rsi_15m"], 1), "RSI 1h": round(item["rsi_1h"], 1),
                              "Illustrative TP1 R:R / اندازاً R:R": "1:{:.2f}".format(item["rr"])})
            except (MarketDataError, requests.RequestException, ValueError) as exc:
                errors.append({"Symbol": symbol, "Error / خرابی": str(exc)})
            progress.progress((index + 1) / len(SUPPORTED_SYMBOLS))
        status.empty()
        st.session_state["scan_table"], st.session_state["scan_errors"] = table, errors
    if "scan_table" in st.session_state:
        if st.session_state["scan_table"]:
            st.dataframe(pd.DataFrame(st.session_state["scan_table"]), use_container_width=True, hide_index=True)
            st.caption("Illustrative target-1 R:R uses fixed ATR multiples, not historical performance. Scores are not win probabilities. / R:R مقررہ ATR تناسب ہے، تاریخی کارکردگی نہیں؛ اسکور جیتنے کا امکان نہیں۔")
        else:
            st.info("No symbols returned analyzable data. / کسی کوائن کا قابلِ تجزیہ ڈیٹا نہیں ملا۔")
        if st.session_state["scan_errors"]:
            st.warning("Some pairs could not be scanned; successful results are still shown. / کچھ کوائن اسکین نہیں ہوئے؛ کامیاب نتائج نیچے موجود ہیں۔")
            st.dataframe(pd.DataFrame(st.session_state["scan_errors"]), use_container_width=True, hide_index=True)

with tab_news:
    st.subheader("Public crypto news / عوامی کرپٹو خبریں")
    st.caption("Headlines link to original publishers. No sentiment or AI classification is applied. / خبریں اصل پبلشر سے منسلک ہیں؛ کوئی AI یا جذباتی درجہ بندی نہیں۔")
    if st.button("Load / refresh news / خبریں لوڈ یا تازہ کریں", use_container_width=True):
        cached_news.clear()
        st.session_state["news_data"] = cached_news()
    news = st.session_state.get("news_data")
    if news is None:
        st.info("Select Load / refresh news to retrieve current headlines. / تازہ خبریں دیکھنے کے لیے لوڈ کا بٹن دبائیں۔")
    elif news["articles"]:
        for article in news["articles"]:
            st.link_button(article["title"], article["url"], use_container_width=True)
            st.caption("{} / ماخذ · {} / اشاعت".format(article["source"], article["published"]))
    else:
        st.info("No headlines are currently available from the configured feeds. / منتخب نیوز فیڈز سے اس وقت خبریں دستیاب نہیں۔")
    if news and news["errors"]:
        with st.expander("Feed availability details / فیڈ کی دستیابی"):
            for error in news["errors"]:
                st.warning(error)

st.markdown("---")
st.caption("Educational market-data tool only; not investment advice. It never places orders. Use at your own risk. / یہ تعلیمی مارکیٹ ڈیٹا ٹول ہے، سرمایہ کاری کا مشورہ نہیں اور کوئی آرڈر نہیں دیتا۔")
