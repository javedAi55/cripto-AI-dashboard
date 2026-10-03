import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd

# 1. Page Configuration (Premium Look)
st.set_page_config(
    page_title="Pro Crypto AI Predictor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Function to Auto-Fetch Top Volume Coins from Binance
@st.cache_data(ttl=300) # 5 منٹ تک ڈیٹا کیش کرے گا تاکہ ویب سائٹ سلو نہ ہو
def get_top_volume_coins():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        res = requests.get(url, timeout=5).json()
        usdt_pairs = [x for x in res if x['symbol'].endswith('USDT') and 'UP' not in x['symbol'] and 'DOWN' not in x['symbol']]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
        return [f"{x['symbol'][: -4]}/{x['symbol'][-4:]}" for x in sorted_pairs[:10]]
    except:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]

# 3. AI Analysis Function
def get_ai_analysis(symbol, interval="15m"):
    clean_sym = symbol.replace("/", "")
    urls = [
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
        
        current_price = df['close'].iloc[-1]
        
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
        
        # Logic
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

        # Signal Output Generation
        is_bullish = bull_prob >= 60
        is_bearish = bear_prob >= 60
        
        candle_pred = "🟢 GREEN (Bullish)" if is_bullish else "🔴 RED (Bearish)" if is_bearish else "⚖️ NEUTRAL"
        pred_prob = bull_prob if is_bullish else bear_prob if is_bearish else 50
        
        if bull_prob >= 65:
            sig = "LONG 🟢"
            tp1, tp2, sl = current_price * 1.015, current_price * 1.025, current_price * 0.985
        elif bear_prob >= 65:
            sig = "SHORT 🔴"
            tp1, tp2, sl = current_price * 0.985, current_price * 0.975, current_price * 1.015
        else:
            sig = "WAIT ⏳"
            tp1 = tp2 = sl = current_price

        return {
            "success": True, "price": current_price, "rsi": current_rsi, "signal": sig,
            "candle_pred": candle_pred, "pred_prob": pred_prob, "reasons": reasons,
            "tp1": tp1, "tp2": tp2, "sl": sl, "bull_prob": bull_prob, "bear_prob": bear_prob
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Sidebar (Settings) ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/1/12/Binance_logo.svg", width=150)
st.sidebar.title("⚙️ کنٹرول پینل")

st.sidebar.markdown("### 🔍 کوائن سلیکشن")
selection_mode = st.sidebar.radio("کوائن کیسے منتخب کریں؟", ["آٹو ٹرینڈنگ (Top Volume)", "اپنی مرضی سے (Custom)"])

if selection_mode == "آٹو ٹرینڈنگ (Top Volume)":
    top_coins = get_top_volume_coins()
    coin_pair = st.sidebar.selectbox("🔥 ٹاپ 10 والیوم کوائنز:", top_coins)
else:
    custom_list = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "DOGE/USDT", "PEPE/USDT", "SHIB/USDT", "ADA/USDT", "INJ/USDT", "LINK/USDT"]
    coin_pair = st.sidebar.selectbox("🪙 اپنی مرضی کا کوائن چنیں:", custom_list)

timeframe = st.sidebar.selectbox("⏱️ کینڈل ٹائم فریم", ["15m (Scalping)", "1h (Day Trading)"])
clean_symbol = coin_pair.replace("/", "")
tf_param = "15m" if "15m" in timeframe else "1h"

# --- Main Dashboard ---
st.title(f"⚡ {coin_pair} پریمیم AI سگنل ڈیش بورڈ")
st.markdown("آرٹیفیشل انٹیلیجنس اور تکنیکی انڈیکیٹرز کی مدد سے لائیو مارکیٹ تجزیہ۔")

if st.button("🤖 لائیو اینالیسس اور سگنل جنریٹ کریں", type="primary", use_container_width=True):
    with st.spinner(f"{coin_pair} کا لائیو ڈیٹا بینانس سے لایا جا رہا ہے..."):
        res = get_ai_analysis(clean_symbol, tf_param)
        if res["success"]:
            st.session_state["analysis"] = res
        else:
            st.error(res["error"])

if "analysis" in st.session_state:
    data = st.session_state["analysis"]
    
    st.markdown("---")
    
    # Premium Metric Cards
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 موجودہ قیمت (Live Price)", f"${data['price']:,.4f}")
    c2.metric("🔮 اگلی کینڈل (Next Candle)", data["candle_pred"])
    c3.metric("🎯 سگنل کی طاقت (Strength)", f"{data['pred_prob']}%")
    
    st.progress(data["bull_prob"] / 100)
    st.caption(f"📈 🟢 Bullish: {data['bull_prob']}%  |  📉 🔴 Bearish: {data['bear_prob']}%")
    
    st.markdown("### 📊 تکنیکی وجوہات (Technical Analysis)")
    for r in data["reasons"]:
        st.write(f"👉 {r}")

    st.markdown("---")
    st.markdown("### 🎯 پروفیشنل ٹریڈ سیٹ اپ")
    
    tc1, tc2, tc3 = st.columns(3)
    tc1.success(f"**Target 1 (TP1):**\n${data['tp1']:,.4f}")
    tc2.success(f"**Target 2 (TP2):**\n${data['tp2']:,.4f}")
    tc3.error(f"**Stop Loss (SL):**\n${data['sl']:,.4f}")

    # Auto-Generated Binance Square Post
    with st.expander("📢 بینانس اسکوائر پوسٹ کاپی کریں (Binance Square Post)"):
        post_text = f"""🚨 {coin_pair} {tf_param} AI Trading Setup 🚨

🔮 Trend Prediction: {data['candle_pred']} ({data['pred_prob']}% Strength)
💵 Current Price: ${data['price']:,.4f}

🎯 TP1: ${data['tp1']:,.4f}
🎯 TP2: ${data['tp2']:,.4f}
🛑 SL: ${data['sl']:,.4f}

📊 AI Insights:
- RSI: {data['rsi']:.1f}

🔗 Trade on Binance using my link:
https://web3.binance.com/m/referral?ref=ZNV91XU8

#Crypto #Binance #{clean_symbol} #TradingSignals"""
        st.code(post_text, language="markdown")

# --- Live TradingView Chart ---
st.markdown("---")
st.markdown(f"### 📈 {coin_pair} لائیو چارٹ (TradingView)")
tv_widget = f"""
<div class="tradingview-widget-container" style="height:550px;width:100%;">
  <div id="tradingview_chart" style="height:550px;width:100%;"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "autosize": true,
    "symbol": "BINANCE:{clean_symbol}",
    "interval": "{15 if tf_param == '15m' else 60}",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "enable_publishing": false,
    "backgroundColor": "#131722",
    "gridColor": "#1f293d",
    "hide_top_toolbar": false,
    "hide_legend": false,
    "save_image": false,
    "container_id": "tradingview_chart"
  }});
  </script>
</div>
"""
components.html(tv_widget, height=580)




