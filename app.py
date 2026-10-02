import streamlit as st
import streamlit.components.v1 as components

# Page Configuration
st.set_page_config(
    page_title="Crypto AI Futures Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Sidebar Settings
st.sidebar.title("⚙️️ Settings / سیٹنگز")

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

# TradingView Binance Live Chart
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
    st.link_button(f"🟡 Trade {coin_pair} on Binance", f"https://www.binance.com/en/futures/{clean_symbol}", use_container_width=True)
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


