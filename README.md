import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Crypto AI Futures Dashboard", layout="wide")

st.title("🤖 SOL/USDT AI Futures Trading Dashboard")
st.caption("سولانا (SOL) فیوچرز ٹریڈنگ کا خودکار AI تجزیہ اور رسک مینجمنٹ ڈیش بورڈ")

# Sidebar for settings
st.sidebar.header("⚙️ ٹریڈنگ سیٹنگز (Settings)")
capital = st.sidebar.number_input("آپ کا ٹوٹل کیپیٹل ($)", value=100.0, step=10.0)
risk_pct = st.sidebar.slider("رسک فی ٹریڈ (%)", 1.0, 5.0, 2.0)
leverage = st.sidebar.slider("لیوریج (Leverage)", 1, 5, 3)

# Data Fetching
@st.cache_data(ttl=60)
def load_data():
    df = yf.download(tickers="SOL-USD", period="7d", interval="1h", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    df['close'] = df['Close'].astype(float)
    
    # RSI Calculation
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # EMA Calculation
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    return df

try:
    df = load_data()
    curr_price = df['close'].iloc[-1]
    curr_rsi = df['RSI'].iloc[-1]
    ema20 = df['EMA_20'].iloc[-1]
    ema50 = df['EMA_50'].iloc[-1]
    ema200 = df['EMA_200'].iloc[-1]

    # Top Metrics Cards
    col1, col2, col3 = st.columns(3)
    col1.metric("موجودہ قیمت (Price)", f"${curr_price:.2f}")
    col2.metric("RSI (14)", f"{curr_rsi:.1f}")
    
    try:
        fg_res = requests.get("https://api.alternative.me/fng/", timeout=3).json()
        fg_val = fg_res['data'][0]['value']
        fg_status = fg_res['data'][0]['value_classification']
        col3.metric("Fear & Greed Index", f"{fg_val} ({fg_status})")
    except:
        col3.metric("Fear & Greed Index", "50 (Neutral)")

    st.markdown("---")

    # AI Futures Signal Analysis
    st.subheader("🎯 AI Futures Trade Signal & Levels")
    
    if curr_rsi > 70:
        signal = "SHORT"
        entry_zone = f"${curr_price:.2f} -${curr_price * 1.01:.2f}"
        sl = curr_price * 1.02
        tp1 = curr_price * 0.97
        tp2 = curr_price * 0.95
        st.error(f"🔴 سگنل: **{signal}** (Overbought زون — ریجیکشن کی تصدیق کریں)")
    elif curr_rsi < 30:
        signal = "LONG"
        entry_zone = f"${curr_price * 0.99:.2f} -${curr_price:.2f}"
        sl = curr_price * 0.98
        tp1 = curr_price * 1.03
        tp2 = curr_price * 1.05
        st.success(f"🟢 سگنل: **{signal}** (Oversold زون — سپورٹ کی تصدیق کریں)")
    else:
        signal = "NEUTRAL"
        entry_zone = "انتظار کریں (No Entry)"
        sl, tp1, tp2 = 0.0, 0.0, 0.0
        st.warning("🟡 سگنل: **NEUTRAL** (مارکیٹ رینج میں ہے، فی الحال ٹریڈ نہ کریں)")

    # Levels Table
    if signal != "NEUTRAL":
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.info(f"📍 **Entry Zone:**\n{entry_zone}")
        col_b.error(f"🛑 **Stop Loss (SL):**\n${sl:.2f}")
        col_c.success(f"🎯 **Target 1 (TP1):**\n${tp1:.2f}")
        col_d.success(f"🎯 **Target 2 (TP2):**\n${tp2:.2f}")

    st.markdown("---")

    # Interactive Chart
    st.subheader("📈 لائیو کینڈل اسٹک اور EMA چارٹ")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df['Datetime'] if 'Datetime' in df else df.index,
                    open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='SOL'))
    fig.add_trace(go.Scatter(x=df['Datetime'] if 'Datetime' in df else df.index, y=df['EMA_20'], line=dict(color='orange', width=1), name='EMA 20'))
    fig.add_trace(go.Scatter(x=df['Datetime'] if 'Datetime' in df else df.index, y=df['EMA_50'], line=dict(color='purple', width=1), name='EMA 50'))
    fig.add_trace(go.Scatter(x=df['Datetime'] if 'Datetime' in df else df.index, y=df['EMA_200'], line=dict(color='blue', width=1), name='EMA 200'))
    fig.update_layout(xaxis_rangeslider_visible=False, height=450, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # Risk Management Calculator
    st.markdown("---")
    st.subheader("🧮 فیوچرز پوزیشن سائز کیلکولیٹر (Futures Risk Calculator)")
    max_risk_usd = (capital * risk_pct) / 100
    st.write(f"💡 **آپ کی پالیسی:** اس ٹریڈ میں آپ کا زیادہ سے زیادہ نقصان **${max_risk_usd:.2f}** سے زیادہ نہیں ہونا چاہیے۔")
    
    if signal != "NEUTRAL" and sl > 0:
        price_diff = abs(curr_price - sl)
        pos_size_sol = max_risk_usd / price_diff
        margin_required = (pos_size_sol * curr_price) / leverage
        
        st.write(f"👉 **تجویز کردہ ٹریڈ سائز:** `{pos_size_sol:.2f} SOL` (${pos_size_sol * curr_price:.2f})")
        st.write(f"👉 **ضروری مارجن ({leverage}x Leverage):** `${margin_required:.2f}`")

except Exception as e:
        st.error(f"ڈاٹا لوڈ کرنے میں مسئلہ آیا: {e}")
