import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Crypto AI Futures & Candle Predictor",
    page_icon="⚡",
    layout="wide"
)

# Function to fetch Binance Data & Calculate Advanced Signal + Candle Prediction
def get_ai_analysis(symbol, interval="15m"):
    urls = [
        f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit=100",
        f"https://api1.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100",
        f"https://api3.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
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
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        current_price = df['close'].iloc[-1]
        
        # 1. RSI Calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # 2. MACD Calculation
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        current_dif = dif.iloc[-1]
        current_dea = dea.iloc[-1]
        
        # 3. EMA 20 & 50 Trend
        ema20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
        
        # Next Candle Prediction Logic (Probability Score)
        bullish_score = 0
        bearish_score = 0
        reasons = []

        # RSI Checks
        if current_rsi < 35:
            bullish_score += 35
            reasons.append(f"RSI Oversold ({current_rsi:.1f}) - بائنگ پریشر کی توقع")
        elif current_rsi > 65:
            bearish_score += 35
            reasons.append(f"RSI Overbought ({current_rsi:.1f}) - سیلنگ پریشر کی توقع")
        else:
            if current_rsi > 50:
                bullish_score += 15
            else:
                bearish_score += 15

        # MACD Checks
        if current_dif > current_dea:
            bullish_score += 30
            reasons.append("MACD Bullish Crossover (DIF > DEA)")
        else:
            bearish_score += 30
            reasons.append("MACD Bearish Crossover (DIF < DEA)")

        # EMA Trend Check
        if current_price > ema20:
            bullish_score += 25
            reasons.append("قیمت EMA(20) سے اوپر ہے (Upward Trend)")
        else:
            bearish_score += 25
            reasons.append("قیمت EMA(20) سے نیچے ہے (Downward Trend)")

        # Normalize Probability
        total = bullish_score + bearish_score
        bull_prob = int((bullish_score / total) * 100) if total > 0 else 50
        bear_prob = 100 - bull_prob

        if bull_prob >= 60:
            candle_pred = "🟢 GREEN CANDLE (Bullish)"
            pred_color = "green"
            pred_prob = bull_prob
        elif bear_prob >= 60:
            candle_pred = "🔴 RED CANDLE (Bearish)"
            pred_color = "red"
            pred_prob = bear_prob
        else:
            candle_pred = "⚖️ SIDEWAYS / NEUTRAL"
            pred_color = "orange"
            pred_prob = 50

        # Signal Logic
        if bull_prob >= 65:
            signal_type = "LONG 🟢"
            entry_low = current_price
            entry_high = current_price * 1.0015
            tp1 = current_price * 1.012
            tp2 = current_price * 1.025
            sl = current_price * 0.988
        elif bear_prob >= 65:
            signal_type = "SHORT 🔻"
            entry_low = current_price
            entry_high = current_price * 1.0015
            tp1 = current_price * 0.988
            tp2 = current_price * 0.975
            sl = current_price * 1.012
        else:
            signal_type = "WAIT ⏳ (انتقال زون)"
            entry_low = current_price
            entry_high = current_price
            tp1 = current_price
            tp2 = current_price
            sl = current_price

        return {
            "success": True,
            "price": current_price,
            "rsi": current_rsi,
            "signal": signal_type,
            "candle_pred": candle_pred,
            "pred_color": pred_color,
            "pred_prob": pred_prob,
            "reasons": reasons,
            "entry_low": entry_low,
            "entry_high": entry_high,
            "tp1": tp1,
            "tp2": tp2,
            "sl": sl,
            "bull_prob": bull_prob,
            "bear_prob": bear_prob
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Sidebar Controls
st.sidebar.title("⚙️️ سیٹنگز (Settings)")
coin_pair = st.sidebar.selectbox("🪙 کوائن منتخب کریں", ["SOL/USDT", "BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT"])
timeframe = st.sidebar.selectbox("⏱️ کینڈل ٹائم فریم (Timeframe)", ["15m (بہترین فورن ٹریڈ)", "1h (زیادہ کنفرم)"], index=0)
clean_symbol = coin_pair.replace("/", "")
tf_param = "15m" if "15m" in timeframe else "1h"

st.sidebar.markdown("---")
st.sidebar.subheader("💰 پوزیشن سائز کیلکولیٹر")
capital = st.sidebar.number_input("کل سرمایہ ($)", min_value=10.0, value=100.0, step=10.0)
risk_pct = st.sidebar.slider("فی ٹریڈ رسک (%)", min_value=0.5, max_value=5.0, value=2.0)
leverage = st.sidebar.slider("لیوریج (Leverage)", min_value=1, max_value=20, value=3)

# Dashboard Title
st.title(f"⚡ {coin_pair} AI کینڈل پریڈکٹر اور ٹریڈنگ ڈیش بورڈ")
st.caption(f"لائیو بینانس ڈیٹا | ٹائم فریم: {tf_param}")

st.markdown("---")
st.subheader("🔮 اگلی کینڈل کا AI اندازہ (Next Candle Predictor)")

if st.button("🤖 لائیو کینڈل اور ٹریڈ سگنل چیک کریں", type="primary", use_container_width=True):
    with st.spinner("بینانس کینڈلز اور انڈیکیٹرز کا تجزیہ ہو رہا ہے..."):
        res = get_ai_analysis(clean_symbol, tf_param)
        if res["success"]:
            st.session_state["analysis"] = res
        else:
            st.error(res["error"])

if "analysis" in st.session_state:
    data = st.session_state["analysis"]
    
    # Candle Prediction Banner
    col1, col2, col3 = st.columns(3)
    col1.metric("موجودہ قیمت (Price)", f"${data['price']:.2f}")
    col2.metric("اگلی کینڈل کا امکان", data["candle_pred"])
    col3.metric("امکان کی شرح (Probability)", f"{data['pred_prob']}%")
    
    st.progress(data["bull_prob"] / 100)
    st.caption(f"📈 🟢 Bullish Probability: {data['bull_prob']}%  |  📉 🔴 Bearish Probability: {data['bear_prob']}%")
    
    st.markdown("#### 🔍 تکنیکی دلائل (Technical Reasons):")
    for r in data["reasons"]:
        st.write(f"• {r}")

    st.markdown("---")
    st.subheader("🎯 مجوزہ AI ٹریڈنگ سگنل")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.info(f"📍 **Entry Zone:**\n${data['entry_low']:.2f} - ${data['entry_high']:.2f}")
    c2.success(f"🎯 **Target 1:**\n${data['tp1']:.2f}")
    c3.success(f"🎯 **Target 2:**\n${data['tp2']:.2f}")
    c4.error(f"🛑 **Stop Loss:**\n${data['sl']:.2f}")

    # Binance Square Ready Post
    st.markdown("---")
    st.markdown("### 📢 بینانس اسکوائر پوسٹ (1-Click Copy)")
    post_text = f"""🚨 {coin_pair} ({tf_param}) Candle & Trade Analysis 🚨

🔮 Next Candle Projection: {data['candle_pred']} ({data['pred_prob']}% Probability)
📍 Entry Zone: ${data['entry_low']:.2f} - ${data['entry_high']:.2f}

🎯 TP1: ${data['tp1']:.2f} | 🎯 TP2: ${data['tp2']:.2f}
🛑 SL: ${data['sl']:.2f}

📊 RSI: {data['rsi']:.1f}

👇 Trade on Binance:
https://web3.binance.com/m/referral?ref=ZNV91XU8

#Crypto #Binance #{clean_symbol} #Signals"""

    st.code(post_text, language="markdown")

# Live TradingView Chart
st.markdown("---")
st.subheader("📈 بینانس لائیو چارٹ")
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



