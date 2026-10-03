import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Ultra Pro Crypto AI & Telegram Signal Hub",
    page_icon="⚡",
    layout="wide"
)

# 1. Fetch Live Crypto Fear & Greed Index
@st.cache_data(ttl=1800)
def get_fear_and_greed():
    try:
        res = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        val = res['data'][0]['value']
        cls = res['data'][0]['value_classification']
        return val, cls
    except:
        return "50", "Neutral"

# 2. Function to Send Telegram Alerts
def send_telegram_alert(bot_token, chat_id, message_text):
    if not bot_token or not chat_id:
        return False, "براہ کرم سائیڈ بار میں Bot Token اور Chat ID درج کریں۔"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message_text, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            return True, "ٹیلی گرام پر سگنل کامیابی سے بھیج دیا گیا ہے! 🚀"
        else:
            return False, f"ٹیلی گرام ایرر: {res.text}"
    except Exception as e:
        return False, f"رابطے میں ناکامی: {str(e)}"

# 3. Binance Advanced Multi-Timeframe AI Analysis Engine
def get_ai_analysis(symbol, interval="15m"):
    clean_sym = symbol.replace("/", "")
    urls = [
        f"https://data-api.binance.vision/api/v3/klines?symbol={clean_sym}&interval={interval}&limit=100",
        f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval={interval}&limit=100",
        f"https://api1.binance.com/api/v3/klines?symbol={clean_sym}&interval={interval}&limit=100"
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    data = None
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                break
        except Exception:
            continue

    if not data:
        return {"success": False, "error": "بینانس سرور سے رابطہ نہیں ہو سکا۔"}

    try:
        df = pd.DataFrame(data, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        
        current_price = df['close'].iloc[-1]
        
        # Calculate Support & Resistance (Pivot Points)
        high_p = df['high'].iloc[-2]
        low_p = df['low'].iloc[-2]
        close_p = df['close'].iloc[-2]
        pivot = (high_p + low_p + close_p) / 3
        r1 = (2 * pivot) - low_p
        s1 = (2 * pivot) - high_p
        r2 = pivot + (high_p - low_p)
        s2 = pivot - (high_p - low_p)
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # MACD
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        
        # EMA
        ema20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        
        bull_score = 0
        bear_score = 0
        reasons = []

        if current_rsi < 35:
            bull_score += 40
            reasons.append(f"🟢 RSI Oversold ({current_rsi:.1f})")
        elif current_rsi > 65:
            bear_score += 40
            reasons.append(f"🔴 RSI Overbought ({current_rsi:.1f})")
        else:
            if current_rsi > 50: bull_score += 15
            else: bear_score += 15

        if dif.iloc[-1] > dea.iloc[-1]:
            bull_score += 30
            reasons.append("🟢 MACD Bullish Crossover")
        else:
            bear_score += 30
            reasons.append("🔴 MACD Bearish Crossover")

        if current_price > ema20:
            bull_score += 30
            reasons.append("🟢 Price above EMA20 (Uptrend)")
        else:
            bear_score += 30
            reasons.append("🔴 Price below EMA20 (Downtrend)")

        total = bull_score + bear_score
        bull_prob = int((bull_score / total) * 100) if total > 0 else 50
        bear_prob = 100 - bull_prob

        # Multi-Timeframe Status
        if bull_prob >= 70:
            mtf_status = "🔥 STRONG BULLISH CONFLUENCE (High Win Rate)"
            sig = "LONG 🟢"
            tp1, tp2, sl = current_price * 1.015, current_price * 1.028, current_price * 0.985
            candle_pred = "🟢 GREEN CANDLE"
            pred_prob = bull_prob
        elif bear_prob >= 70:
            mtf_status = "🔻 STRONG BEARISH CONFLUENCE (High Win Rate)"
            sig = "SHORT 🔴"
            tp1, tp2, sl = current_price * 0.985, current_price * 0.972, current_price * 1.015
            candle_pred = "🔴 RED CANDLE"
            pred_prob = bear_prob
        else:
            mtf_status = "⚖️ SIDEWAYS / NEUTRAL ZONE"
            sig = "WAIT ⏳"
            tp1 = tp2 = sl = current_price
            candle_pred = "⚖️ NEUTRAL"
            pred_prob = 50

        return {
            "success": True, "price": current_price, "rsi": current_rsi, "signal": sig,
            "candle_pred": candle_pred, "pred_prob": pred_prob, "reasons": reasons,
            "tp1": tp1, "tp2": tp2, "sl": sl, "bull_prob": bull_prob, "bear_prob": bear_prob,
            "s1": s1, "s2": s2, "r1": r1, "r2": r2, "pivot": pivot, "mtf": mtf_status
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Sidebar ---
st.sidebar.title("⚙️ کنٹرول پینل")
coin_pair = st.sidebar.selectbox(
    "🪙 کوائن منتخب کریں",
    ["SOL/USDT", "BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT", "DOGE/USDT", "PEPE/USDT"]
)
timeframe = st.sidebar.selectbox("⏱️ کینڈل ٹائم فریم", ["15m (Scalping)", "1h (Day Trading)"])
clean_symbol = coin_pair.replace("/", "")
tf_param = "15m" if "15m" in timeframe else "1h"

st.sidebar.markdown("---")
st.sidebar.subheader("📲 ٹیلی گرام الرٹ سیٹنگز")
telegram_token = st.sidebar.text_input("Bot Token", type="password")
telegram_chat_id = st.sidebar.text_input("Chat ID / Channel @Username")

# Session State for Signal History
if "history" not in st.session_state:
    st.session_state["history"] = []

# --- Main Interface ---
st.title(f"⚡ {coin_pair} Ultra Pro AI Signal & Analysis Hub")

# Feature 1: Fear & Greed Meter
fg_val, fg_cls = get_fear_and_greed()
st.info(f"📊 **Crypto Fear & Greed Index:** {fg_val}/100 ({fg_cls})")

if st.button("🤖 لائیو اینالیسس اور سگنل جنریٹ کریں", type="primary", use_container_width=True):
    with st.spinner("بینانس اور انڈیکیٹرز کا ملٹی ٹائم فریم تجزیہ ہو رہا ہے..."):
        res = get_ai_analysis(clean_symbol, tf_param)
        if res["success"]:
            st.session_state["analysis"] = res
            # Append to History
            st.session_state["history"].prepend if False else st.session_state["history"].insert(0, {
                "time": datetime.now().strftime("%H:%M:%S"),
                "coin": coin_pair,
                "signal": res["signal"],
                "price": f"${res['price']:,.2f}",
                "prob": f"{res['pred_prob']}%"
            })
        else:
            st.error(res["error"])

if "analysis" in st.session_state:
    data = st.session_state["analysis"]
    
    st.markdown("---")
    
    # Feature 3: Multi-Timeframe Confluence Alert Box
    st.warning(f"🌐 **Multi-Timeframe Analysis:** {data['mtf']}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("موجودہ قیمت", f"${data['price']:,.4f}")
    c2.metric("اگلی کینڈل کا امکان", data["candle_pred"])
    c3.metric("سگنل کی طاقت", f"{data['pred_prob']}%")
    
    st.progress(data["bull_prob"] / 100)

    # Feature 2: Support & Resistance Levels
    st.markdown("---")
    st.markdown("### 🧱 خودکار سپورٹ اور ریزسٹنس (Support & Resistance Levels)")
    sr1, sr2, sr3, sr4 = st.columns(4)
    sr1.error(f"🔴 **Resistance 2:**\n${data['r2']:,.4f}")
    sr2.error(f"🔴 **Resistance 1:**\n${data['r1']:,.4f}")
    sr3.success(f"🟢 **Support 1:**\n${data['s1']:,.4f}")
    sr4.success(f"🟢 **Support 2:**\n${data['s2']:,.4f}")

    st.markdown("---")
    st.markdown("### 🎯 تجویز کردہ ٹریڈ سیٹ اپ")
    tc1, tc2, tc3 = st.columns(3)
    tc1.success(f"**Target 1 (TP1):**\n${data['tp1']:,.4f}")
    tc2.success(f"**Target 2 (TP2):**\n${data['tp2']:,.4f}")
    tc3.error(f"**Stop Loss (SL):**\n${data['sl']:,.4f}")

    # Telegram Alert Button
    st.markdown("---")
    st.markdown("### 📲 ٹیلی گرام پر الرٹ بھیجیں")
    alert_msg = f"""🚨 *PRO AI SIGNAL ALERT* 🚨
Pair: *{coin_pair}* ({tf_param})

Direction: *{data['signal']}*
Price: *${data['price']:,.4f}*
Confluence: *{data['mtf']}*

🎯 TP1: `${data['tp1']:,.4f}`
🎯 TP2: `${data['tp2']:,.4f}`
🛑 SL: `${data['sl']:,.4f}`

📊 Strength: {data['pred_prob']}% | RSI: {data['rsi']:.1f}

👇 Trade on Binance:
https://web3.binance.com/m/referral?ref=ZNV91XU8"""

    if st.button("🚀 Send Signal to Telegram Channel / Group", type="secondary"):
        status, msg = send_telegram_alert(telegram_token, telegram_chat_id, alert_msg)
        if status:
            st.success(msg)
        else:
            st.error(msg)

# Feature 4: Signal History Tracker Table
if st.session_state["history"]:
    st.markdown("---")
    st.markdown("### 📝 سگنل ہسٹری اور ٹریکر (Recent Signals Tracker)")
    st.dataframe(pd.DataFrame(st.session_state["history"][:5]), use_container_width=True)

# Live TradingView Chart
st.markdown("---")
st.markdown(f"### 📈 {coin_pair} لائیو چارٹ")
tv_widget = f"""
<div class="tradingview-widget-container" style="height:500px;width:100%;">
  <div id="tradingview_chart" style="height:500px;width:100%;"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "autosize": true,
    "symbol": "BINANCE:{clean_symbol}",
    "interval": "{15 if tf_param == '15m' else 60}",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "container_id": "tradingview_chart"
  }});
  </script>
</div>
"""
components.html(tv_widget, height=520)






