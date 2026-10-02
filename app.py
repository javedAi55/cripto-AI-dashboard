import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Crypto AI Futures Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Function to fetch Binance Klines with Fallbacks and calculate indicators
def get_ai_signal(symbol):
    urls = [
        f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval=15m&limit=50",
        f"https://api1.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=50",
        f"https://api3.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=50"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    
    data = None
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                break
        except Exception:
            continue

    if not data:
        return {"success": False, "error": "Unable to connect to Binance market servers."}

    try:
        df = pd.DataFrame(data, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        
        current_price = df['close'].iloc[-1]
        h24 = df['high'].max()
        l24 = df['low'].min()
        
        # Calculate EMA
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        ema9 = df['ema9'].iloc[-1]
        ema21 = df['ema21'].iloc[-1]
        
        # Signal Decision
        if current_rsi > 60 or ema9 < ema21:
            signal_type = "SHORT 🔻"
            tp1 = current_price * 0.985
            tp2 = current_price * 0.970
            sl = current_price * 1.015
            reason = f"RSI: {current_rsi:.1f} (Bearish Reversal / EMA Downtrend)"
            confidence = min(95, int(65 + abs(current_rsi - 50) + (10 if ema9 < ema21 else 0)))
            risk = sl - current_price
            reward = current_price - tp1
            rr_ratio = f"1 : {abs(reward/risk):.1f}" if risk != 0 else "1 : 1.5"
        else:
            signal_type = "LONG 🟢"
            tp1 = current_price * 1.015
            tp2 = current_price * 1.030
            sl = current_price * 0.985
            reason = f"RSI: {current_rsi:.1f} (Bullish Reversal / EMA Uptrend)"
            confidence = min(95, int(65 + abs(50 - current_rsi) + (10 if ema9 > ema21 else 0)))
            risk = current_price - sl
            reward = tp1 - current_price
            rr_ratio = f"1 : {abs(reward/risk):.1f}" if risk != 0 else "1 : 1.5"
            
        return {
            "success": True,
            "price": current_price,
            "h24": h24,
            "l24": l24,
            "signal": signal_type,
            "tp1": tp1,
            "tp2": tp2,
            "sl": sl,
            "reason": reason,
            "confidence": confidence,
            "rsi": current_rsi,
            "rr_ratio": rr_ratio
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Sidebar Settings
st.sidebar.title("⚙ Settings / سیٹنگز")

# Language Selection
lang = st.sidebar.radio("🌐 Select Language / زبان منتخب کریں", ["Urdu (اردو)", "English"])

# Coin Selection
coin_pair = st.sidebar.selectbox(
    "🪙 Select Crypto Pair / کوائن منتخب کریں",
    ["SOL/USDT", "BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT"]
)

clean_symbol = coin_pair.replace("/", "")

# Risk Management Settings
st.sidebar.markdown("---")
st.sidebar.subheader("💰 Risk Management / رسک مینجمنٹ")
capital = st.sidebar.number_input("Capital ($) / کل سرمایہ", min_value=10.0, value=100.0, step=10.0)
risk_pct = st.sidebar.slider("Risk per Trade (%) / فی ٹریڈ رسک", min_value=0.5, max_value=5.0, value=2.0, step=0.5)
leverage = st.sidebar.slider("Leverage (x) / لیوریج", min_value=1, max_value=50, value=3)

# Main Header
if lang == "Urdu (اردو)":
    st.title(f"⚡ {coin_pair} AI فیوچرز ٹریڈنگ ڈیش بورڈ")
    st.caption("بینانس لائیو ٹریڈنگ ویو چارٹ، AI سگنلز اور فیوچرز رسک کیلکولیٹر")
else:
    st.title(f"⚡ {coin_pair} AI Futures Trading Dashboard")
    st.caption("Binance Live TradingView Chart, AI Signals & Futures Risk Calculator")

# AI Signal Section
st.markdown("---")
if lang == "Urdu (اردو)":
    st.subheader("🎯 AI لائیو ٹریڈنگ سگنل (Live AI Signal)")
    btn_label = f"🤖 {coin_pair} کا لائیو سگنل حاصل کریں (Generate Signal)"
else:
    st.subheader("🎯 Live AI Trading Signal")
    btn_label = f"🤖 Generate {coin_pair} Signal"

if st.button(btn_label, type="primary", use_container_width=True):
    with st.spinner("Analyzing Binance Market Data..."):
        sig = get_ai_signal(clean_symbol)
        if sig["success"]:
            st.session_state["last_signal"] = sig
        else:
            st.error("مارکیٹ ڈیٹا حاصل کرنے میں مسئلہ آیا۔ براہ کرم دوبارہ کوشش کریں۔")

if "last_signal" in st.session_state:
    sig = st.session_state["last_signal"]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("موجودہ قیمت (Price)", f"${sig['price']:.2f}")
    col2.metric("AI سگنل (Signal)", sig["signal"])
    col3.metric("اعتماد (Confidence)", f"{sig['confidence']}%")
    col4.metric("رسک ریشو (R:R)", sig['rr_ratio'])
    
    st.markdown("### 📋 ٹریڈنگ پلان (Trading Plan):")
    c_tp1, c_tp2, c_sl = st.columns(3)
    c_tp1.success(f"🎯 **Target 1 (TP1):** `${sig['tp1']:.2f}`")
    c_tp2.success(f"🎯 **Target 2 (TP2):** `${sig['tp2']:.2f}`")
    c_sl.error(f"🛑 **Stop Loss (SL):** `${sig['sl']:.2f}`")
    
    st.caption(f"📊 **تکنیکی تجزیہ (Technical Analysis):** {sig['reason']} | RSI: {sig['rsi']:.1f}")
    
    # Binance Square Ready-Made Post Generator
    st.markdown("---")
    st.markdown("### 📢 Binance Square پوسٹ کے لیے ٹیکسٹ (1-Click Copy)")
    post_content = f"""🚨 {coin_pair} AI Futures Trading Signal 🚨

Signal: {sig['signal']}
Price: ${sig['price']:.2f}

🎯 Target 1: ${sig['tp1']:.2f}
🎯 Target 2: ${sig['tp2']:.2f}
🛑 Stop Loss: ${sig['sl']:.2f}

📊 AI Confidence: {sig['confidence']}% | Risk/Reward: {sig['rr_ratio']}

👇 Trade directly on Binance using my VIP link:
https://web3.binance.com/m/referral?ref=ZNV91XU8

#Crypto #Binance #{clean_symbol} #TradingSignals"""

    st.code(post_content, language="markdown")

# TradingView Binance Live Chart
st.markdown("---")
if lang == "Urdu (اردو)":
    st.subheader("📈 بینانس لائیو کینڈل اسٹک چارٹ (Binance Real-Time Chart)")
else:
    st.subheader("📈 Binance Live Candlestick Chart (Real-Time)")

tv_widget_html = f"""
<div class="tradingview-widget-container" style="height:550px;width:100%;">
  <div id="tradingview_chart" style="height:550px;width:100%;"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "autosize": true,
    "symbol": "BINANCE:{clean_symbol}",
    "interval": "15",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "container_id": "tradingview_chart"
  }});
  </script>
</div>
"""
components.html(tv_widget_html, height=560)

# Quick Trade Affiliate Buttons
st.markdown("---")
if lang == "Urdu (اردو)":
    st.subheader("🔗 ایکسچینج پر ٹریڈ شروع کریں")
else:
    st.subheader("🔗 Trade Directly on Exchange")

col1, col2 = st.columns(2)
with col1:
    st.link_button(f"🟡 Trade {coin_pair} on Binance", "https://web3.binance.com/m/referral?ref=ZNV91XU8", use_container_width=True)
with col2:
    st.link_button(f"🖤 Trade {coin_pair} on Bybit", f"https://www.bybit.com/trade/usdt/{clean_symbol}", use_container_width=True)

# Risk & Position Size Calculator
st.markdown("---")
max_loss = capital * (risk_pct / 100)
suggested_position = max_loss * leverage
required_margin = suggested_position / leverage

if lang == "Urdu (اردو)":
    st.subheader("🧮 فیوچرز پوزیشن سائز کیلکولیٹر (Futures Risk Calculator)")
    st.info(f"💡 **رسک پالیسی:** اس ٹریڈ میں آپ کا زیادہ سے زیادہ نقصان **${max_loss:.2f}** سے زیادہ نہیں ہونا چاہیے۔")
    st.write(f"👉 **تجویز کردہ پوزیشن سائز (Position Size):** `${suggested_position:.2f}`")
    st.write(f"👉 **ضروری مارجن ({leverage}x Leverage):** `${required_margin:.2f}`")
else:
    st.subheader("🧮 Futures Position Size Calculator")
    st.info(f"💡 **Risk Rule:** Your maximum loss on this trade should not exceed **${max_loss:.2f}**.")
    st.write(f"👉 **Suggested Position Size:** `${suggested_position:.2f}`")
    st.write(f"👉 **Required Margin ({leverage}x Leverage):** `${required_margin:.2f}`")
