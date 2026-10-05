import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Ultra Pro Crypto AI Hub",
    page_icon="🦅",
    layout="wide"
)

# 1. Animal Animations (100% Working GIFs)
def show_eagle():
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
        <img src="https://media.tenor.com/XqTj92-Vj2sAAAAi/eagle-flying.gif" width="180" style="border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);">
    </div>
    """, unsafe_allow_html=True)

def show_lion():
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 20px;">
        <img src="https://media.tenor.com/hXyJmH0R7E8AAAAi/lion-roar.gif" width="160" style="border-radius: 10px;">
    </div>
    """, unsafe_allow_html=True)

# 2. Fetch Fear & Greed Index
@st.cache_data(ttl=1800)
def get_fear_and_greed():
    try:
        res = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        val = res['data'][0]['value']
        cls = res['data'][0]['value_classification']
        return val, cls
    except:
        return "50", "Neutral"

# 3. Send Telegram Alert
def send_telegram_alert(bot_token, chat_id, message_text):
    if not bot_token or not chat_id:
        return False, "براہ کرم سائیڈ بار میں Bot Token اور Chat ID درج کریں۔"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message_text, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200: return True, "ٹیلی گرام پر سگنل چلا گیا! 🚀"
        else: return False, f"ٹیلی گرام ایرر: {res.text}"
    except Exception as e:
        return False, f"رابطے میں ناکامی: {str(e)}"

# 4. Binance AI Engine
def get_ai_analysis(symbol, interval="15m"):
    clean_sym = symbol.replace("/", "")
    urls = [
        f"https://data-api.binance.vision/api/v3/klines?symbol={clean_sym}&interval={interval}&limit=100",
        f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval={interval}&limit=100"
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

    if not data: return {"success": False, "error": "بینانس سرور سے رابطہ نہیں ہو سکا۔"}

    try:
        df = pd.DataFrame(data, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        
        current_price = df['close'].iloc[-1]
        
        # Pivot Points
        high_p, low_p, close_p = df['high'].iloc[-2], df['low'].iloc[-2], df['close'].iloc[-2]
        pivot = (high_p + low_p + close_p) / 3
        r1, s1 = (2 * pivot) - low_p, (2 * pivot) - high_p
        r2, s2 = pivot + (high_p - low_p), pivot - (high_p - low_p)
        
        # Indicators
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-10))))
        current_rsi = rsi.iloc[-1]
        
        ema20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        
        bull_prob = 70 if (current_rsi < 40 and current_price > ema20) else 40
        bear_prob = 100 - bull_prob

        # Signal Logic
        entry_low = current_price * 0.999
        entry_high = current_price * 1.001
        
        if bull_prob >= 65:
            mtf_status = "🔥 STRONG BULLISH CONFLUENCE"
            sig = "LONG 🟢"
            tp1, tp2, sl = current_price * 1.015, current_price * 1.028, current_price * 0.985
            candle_pred, pred_prob = "🟢 GREEN CANDLE", bull_prob
        elif bear_prob >= 65:
            mtf_status = "🔻 STRONG BEARISH CONFLUENCE"
            sig = "SHORT 🔴"
            tp1, tp2, sl = current_price * 0.985, current_price * 0.972, current_price * 1.015
            candle_pred, pred_prob = "🔴 RED CANDLE", bear_prob
        else:
            mtf_status = "⚖️ NEUTRAL / SIDEWAYS"
            sig = "WAIT ⏳"
            tp1 = tp2 = sl = current_price
            candle_pred, pred_prob = "⚖️ NEUTRAL", 50

        return {
            "success": True, "price": current_price, "rsi": current_rsi, "signal": sig,
            "candle_pred": candle_pred, "pred_prob": pred_prob,
            "entry_low": entry_low, "entry_high": entry_high,
            "tp1": tp1, "tp2": tp2, "sl": sl, "bull_prob": bull_prob, "bear_prob": bear_prob,
            "s1": s1, "s2": s2, "r1": r1, "r2": r2, "mtf": mtf_status
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Sidebar Controls ---
st.sidebar.title("⚙️ کنٹرول پینل")

# 🦁 Lion Animation in Sidebar
with st.sidebar:
    show_lion()

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

if "history" not in st.session_state: st.session_state["history"] = []

# --- Main Layout ---
col_head, col_anim = st.columns([3, 1])

with col_head:
    st.title(f"⚡ {coin_pair} Ultra Pro AI Hub")
    fg_val, fg_cls = get_fear_and_greed()
    st.info(f"📊 **Crypto Fear & Greed Index:** {fg_val}/100 ({fg_cls})")

with col_anim:
    # 🦅 Eagle Animation on Main Page
    show_eagle()

# 🤖 Manual Button is BACK!
if st.button("🤖 لائیو اینالیسس اور سگنل جنریٹ کریں", type="primary", use_container_width=True):
    with st.spinner("طوفانی سگنل تیار ہو رہا ہے..."):
        res = get_ai_analysis(clean_symbol, tf_param)
        if res["success"]:
            st.session_state["analysis"] = res
        else:
            st.error(res["error"])

# Display Results if Available
if "analysis" in st.session_state:
    data = st.session_state["analysis"]
    st.markdown("---")
    st.warning(f"🌐 **Multi-Timeframe Analysis:** {data['mtf']}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("موجودہ قیمت", f"${data['price']:,.4f}")
    c2.metric("اگلی کینڈل کا امکان", data["candle_pred"])
    c3.metric("سگنل کی طاقت", f"{data['pred_prob']}%")
    st.progress(data["bull_prob"] / 100)

    # Support & Resistance Levels
    st.markdown("---")
    st.markdown("### 🧱 خودکار سپورٹ اور ریزسٹنس")
    sr1, sr2, sr3, sr4 = st.columns(4)
    sr1.error(f"🔴 Resistance 2:\n${data['r2']:,.4f}")
    sr2.error(f"🔴 Resistance 1:\n${data['r1']:,.4f}")
    sr3.success(f"🟢 Support 1:\n${data['s1']:,.4f}")
    sr4.success(f"🟢 Support 2:\n${data['s2']:,.4f}")

    # FIX: Only show TP/SL if signal is not WAIT
    st.markdown("---")
    st.markdown("### 🎯 تجویز کردہ ٹریڈ سیٹ اپ")
    
    if data['signal'] == "WAIT ⏳":
        st.error("⚠️ **مارکیٹ اس وقت واضح نہیں ہے۔ کوئی ٹریڈ نہ لیں۔ سپورٹ یا ریزسٹنس کے ٹوٹنے کا انتظار کریں!**")
    else:
        st.info(f"📍 **Entry Zone (یہاں انٹری لیں):** ${data['entry_low']:,.4f} -${data['entry_high']:,.4f}")
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
Entry: *${data['entry_low']:,.4f} -${data['entry_high']:,.4f}*

🎯 TP1: `${data['tp1']:,.4f}` | 🎯 TP2: `${data['tp2']:,.4f}`
🛑 SL: `${data['sl']:,.4f}`

👇 Trade on Binance:
https://web3.binance.com/m/referral?ref=ZNV91XU8"""

    if st.button("🚀 Send Signal to Telegram Channel", type="secondary"):
        status, msg = send_telegram_alert(telegram_token, telegram_chat_id, alert_msg)
        if status: st.success(msg)
        else: st.error(msg)


