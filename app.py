import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Institutional AI Futures Advisor",
    page_icon="🦅",
    layout="wide"
)

# --- Advanced Quant Engine (Binance Vision Node - Never Blocked) ---
def get_institutional_analysis(symbol, interval, capital, risk_pct):
    clean_sym = symbol.replace("/", "")
    
    # Binance Public Vision Data Node (High Availability)
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={clean_sym}&interval={interval}&limit=100"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    data = None
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
    except Exception as e:
        pass

    if not data:
        return {"success": False, "error": "بینانس سرور تک رسائی میں عارضی مسئلہ ہے۔ براہ کرم دوبارہ کوشش کریں۔"}

    try:
        df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'ct', 'qav', 'nt', 'tbv', 'tqv', 'ignore'])
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        current_price = df['close'].iloc[-1]
        
        # 1. Volatility (ATR - Average True Range)
        df['H-L'] = df['high'] - df['low']
        df['H-PC'] = (df['high'] - df['close'].shift(1)).abs()
        df['L-PC'] = (df['low'] - df['close'].shift(1)).abs()
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        atr = df['TR'].rolling(14).mean().iloc[-1]

        # 2. Indicators (RSI, MACD, EMA)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-10)))).iloc[-1]
        
        ema20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
        
        macd_line = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line.iloc[-1] - signal_line.iloc[-1]

        # 3. Setup Quality Scoring (0-100)
        setup_score = 0
        reasons = []
        trade_dir = "NEUTRAL"

        if current_price > ema20 and ema20 > ema50:
            setup_score += 25
            reasons.append("مارکیٹ کا ٹرینڈ Bullish ہے (Price > EMA20 > EMA50)۔")
            trade_dir = "LONG"
        if rsi > 40 and rsi < 70:
            setup_score += 25
            reasons.append(f"RSI ({rsi:.1f}) میں اوپر جانے کی گنجائش موجود ہے۔")
        if macd_hist > 0:
            setup_score += 25
            reasons.append("MACD مومنٹم مثبت (Positive) ہے۔")
        
        bear_score = 0
        bear_reasons = []
        if current_price < ema20 and ema20 < ema50:
            bear_score += 25
            bear_reasons.append("مارکیٹ کا ٹرینڈ Bearish ہے (Price < EMA20 < EMA50)۔")
            trade_dir = "SHORT"
        if rsi < 60 and rsi > 30:
            bear_score += 25
            bear_reasons.append(f"RSI ({rsi:.1f}) میں مزید گرنے کی گنجائش ہے۔")
        if macd_hist < 0:
            bear_score += 25
            bear_reasons.append("MACD مومنٹم منفی (Negative) ہے۔")

        if bear_score > setup_score:
            setup_score = bear_score
            reasons = bear_reasons

        vol_ma = df['volume'].rolling(20).mean().iloc[-1]
        if df['volume'].iloc[-1] > vol_ma:
            setup_score += 25
            reasons.append("حالیہ کینڈل میں والیوم (Volume) معمول سے زیادہ ہے، جو بریک آؤٹ کی تصدیق ہے۔")

        # 4. Risk Management
        if trade_dir == "LONG":
            sl = current_price - (atr * 1.5)
            tp1 = current_price + (atr * 2.0)
            tp2 = current_price + (atr * 3.5)
            entry_zone = f"${current_price * 0.999:.4f} - ${current_price * 1.001:.4f}"
        elif trade_dir == "SHORT":
            sl = current_price + (atr * 1.5)
            tp1 = current_price - (atr * 2.0)
            tp2 = current_price - (atr * 3.5)
            entry_zone = f"${current_price * 1.001:.4f} - ${current_price * 0.999:.4f}"
        else:
            sl = tp1 = tp2 = current_price
            entry_zone = "N/A"

        risk = abs(current_price - sl)
        reward = abs(tp1 - current_price)
        rr_ratio = reward / risk if risk > 0 else 0

        risk_amount = capital * (risk_pct / 100)
        position_size_usd = risk_amount / (risk / current_price) if risk > 0 else 0
        max_leverage = int((position_size_usd / capital) * 1.2) if capital > 0 else 1
        max_leverage = max(1, min(max_leverage, 15)) 

        # 5. Rejection Rules
        final_signal = trade_dir
        warning_msg = ""
        if setup_score < 65:
            final_signal = "WAIT ⏳"
            warning_msg = "سیٹ اپ کوالٹی 65 سے کم ہے۔ ٹریڈ منسوخ کر دی گئی۔"
        elif rr_ratio < 1.3:
            final_signal = "WAIT ⏳"
            warning_msg = f"Risk/Reward ریونیو ({rr_ratio:.2f}) بہت کم ہے۔ ٹریڈ منسوخ!"

        return {
            "success": True, "price": current_price, "signal": final_signal,
            "score": setup_score, "rr": rr_ratio, "reasons": reasons,
            "entry_zone": entry_zone, "tp1": tp1, "tp2": tp2, "sl": sl,
            "pos_size": position_size_usd, "leverage": max_leverage,
            "risk_amt": risk_amount, "warning": warning_msg
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Sidebar ---
st.sidebar.title("⚙️ Risk Engine & Settings")

st.sidebar.markdown("### 🦁 Pro Quant Advisor")
st.sidebar.markdown("---")

st.sidebar.markdown("### 🏦 Portfolio Risk Management")
capital = st.sidebar.number_input("کل سرمایہ (Total Capital $)", min_value=10, value=500, step=50)
risk_pct = st.sidebar.slider("ایک ٹریڈ پر رسک (Risk Per Trade %)", min_value=0.5, max_value=5.0, value=2.0, step=0.5)

st.sidebar.markdown("### 📊 Market Settings")
coin_pair = st.sidebar.selectbox("🪙 کوائن", ["SOL/USDT", "BTC/USDT", "ETH/USDT", "BNB/USDT", "DOGE/USDT"])
timeframe = st.sidebar.selectbox("⏱️️ ٹائم فریم", ["15m", "1h", "4h"])
clean_symbol = coin_pair.replace("/", "")

# --- Main Layout ---
st.title(f"🦅 {coin_pair} Institutional AI Advisor")
st.caption("Advanced Setup Scoring | Strict Risk Management | Futures Volatility Engine")

# Manual Trigger Button
if st.button("🤖 مارکیٹ کا گہرا تجزیہ اور سگنل جنریٹ کریں", type="primary", use_container_width=True):
    with st.spinner("کوانٹ الگورتھم لائیو مارکیٹ اور رسک کا جائزہ لے رہا ہے..."):
        data = get_institutional_analysis(clean_symbol, timeframe, capital, risk_pct)
        
        if not data["success"]:
            st.error(data["error"])
        else:
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("موجودہ قیمت", f"${data['price']:,.4f}")
            c2.metric("حتمی فیصلہ", data["signal"] + (" 🟢" if "LONG" in data["signal"] else " 🔴" if "SHORT" in data["signal"] else ""))
            c3.metric("سیٹ اپ کوالٹی", f"{data['score']}/100")
            c4.metric("Risk/Reward", f"1 : {data['rr']:.2f}")

            st.progress(data["score"] / 100)

            if data["signal"] == "WAIT ⏳":
                st.error(f"⚠️ **ٹریڈ مسترد (TRADE REJECTED):** {data['warning']}")
                st.info("💡 پرو ٹپ: اپنا سرمایہ بچانا بھی ایک بہترین ٹریڈ ہے۔ اچھے سیٹ اپ کا انتظار کریں۔")
            else:
                st.success(f"✅ **پرفیکٹ سیٹ اپ مل گیا!**")
                st.markdown("### 🎯 ٹریڈ کی تفصیلات (Execution Zone)")
                st.info(f"📍 **Entry Zone:** {data['entry_zone']}")
                
                tc1, tc2, tc3 = st.columns(3)
                tc1.success(f"**Target 1 (TP1):**\n${data['tp1']:,.4f}")
                tc2.success(f"**Target 2 (TP2):**\n${data['tp2']:,.4f}")
                tc3.error(f"**Stop Loss (SL):**\n${data['sl']:,.4f}")

                st.markdown("---")
                st.markdown("### 🛡️️ رسک مینجمنٹ پلان (Strict Risk Controls)")
                r1, r2, r3 = st.columns(3)
                r1.warning(f"**نقصان (Max Risk):**\n${data['risk_amt']:.2f}")
                r2.warning(f"**پوزیشن سائز:**\n${data['pos_size']:.2f}")
                r3.warning(f"**محفوظ لیوریج:**\n{data['leverage']}x")

                st.markdown("---")
                st.markdown("### 🧠 یہ ٹریڈ کیوں لی جائے؟")
                for idx, reason in enumerate(data['reasons'], 1):
                    st.write(f"{idx}. {reason}")

