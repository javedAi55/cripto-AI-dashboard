import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Crypto AI Dashboard Pro+", page_icon="₿", layout="wide")
BASE = "https://data-api.binance.vision"
FUTURES = "https://fapi.binance.com"
HEADERS = {"User-Agent": "CryptoAIDashboard/2.0"}
st.markdown("""
<style>
/* Main dashboard */
.stApp {
    background: #f5f7fb;
    color: #1e293b;
}

/* Header */
[data-testid="stHeader"] {
    background: #ffffff;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    color: #1e293b;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    padding: 16px;
    border-radius: 12px;
    box-shadow: 0 3px 10px rgba(15, 23, 42, 0.06);
}

/* Headings */
h1, h2, h3 {
    color: #172b4d;
    font-weight: 700;
}

/* Buttons */
.stButton > button,
.stFormSubmitButton > button {
    background: #2563eb;
    color: #ffffff;
    border: 1px solid #2563eb;
    border-radius: 8px;
    font-weight: 600;
    min-height: 42px;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #1d4ed8;
    color: #ffffff;
    border-color: #1d4ed8;
}

/* Tabs */
div[data-baseweb="tab-list"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 5px;
    gap: 5px;
}

div[data-baseweb="tab"] {
    color: #334155;
}

/* Tables */
[data-testid="stDataFrame"],
[data-testid="stTable"] {
    background: #ffffff;
    border-radius: 10px;
}

/* Input fields */
.stTextInput input,
.stNumberInput input {
    background: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
}

/* Information boxes */
[data-testid="stAlert"] {
    border-radius: 10px;
}

/* Main content spacing */
.block-container {
    padding-top: 1.8rem;
    padding-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

def api(url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def money(v):
    try:
        v=float(v)
        return f"${v:,.2f}" if abs(v)>=1000 else (f"${v:,.4f}" if abs(v)>=1 else f"${v:,.8f}")
    except (TypeError,ValueError):
        return "N/A"

def rsi_calc(s, period=14):
    delta=s.diff()
    gain=delta.clip(lower=0).ewm(alpha=1/period,min_periods=period,adjust=False).mean()
    loss=(-delta.clip(upper=0)).ewm(alpha=1/period,min_periods=period,adjust=False).mean()
    rs=gain/loss.replace(0,np.nan)
    return (100-100/(1+rs)).fillna(50)

@st.cache_data(ttl=10, show_spinner=False)
def candles(symbol, interval):
    raw=api(f"{BASE}/api/v3/klines",{"symbol":symbol,"interval":interval,"limit":300})
    if not isinstance(raw,list) or not raw: return pd.DataFrame()
    cols=["time","open","high","low","close","volume","close_time","quote_volume","trades","taker_buy_base","taker_buy_quote","ignore"]
    d=pd.DataFrame(raw,columns=cols)
    for c in ["open","high","low","close","volume","quote_volume"]: d[c]=pd.to_numeric(d[c],errors="coerce")
    d["time"]=pd.to_datetime(d["time"],unit="ms",utc=True)
    for span in [20,50,200]: d[f"EMA{span}"]=d["close"].ewm(span=span,adjust=False).mean()
    d["RSI"]=rsi_calc(d["close"])
    d["VolumeMA20"]=d["volume"].rolling(20).mean()
    return d.dropna(subset=["close"])

@st.cache_data(ttl=10, show_spinner=False)
def ticker(symbol):
    return api(f"{BASE}/api/v3/ticker/24hr",{"symbol":symbol})
def chart(df, symbol, count, emas):
    d = df.tail(count).copy()

    f = go.Figure()

    # Clear green and red candles
    f.add_trace(go.Candlestick(
        x=d["time"],
        open=d["open"],
        high=d["high"],
        low=d["low"],
        close=d["close"],
        name=symbol,
        increasing=dict(
            line=dict(color="#00A878", width=1.5),
            fillcolor="#00C087"
        ),
        decreasing=dict(
            line=dict(color="#E53950", width=1.5),
            fillcolor="#F6465D"
        ),
        whiskerwidth=0.7
    ))

    # Moving average lines
    if emas:
        f.add_trace(go.Scatter(
            x=d["time"], y=d["EMA20"],
            name="EMA 20",
            line=dict(color="#D99A00", width=2)
        ))

        f.add_trace(go.Scatter(
            x=d["time"], y=d["EMA50"],
            name="EMA 50",
            line=dict(color="#2563EB", width=2)
        ))

        if len(df) >= 200:
            f.add_trace(go.Scatter(
                x=d["time"], y=d["EMA200"],
                name="EMA 200",
                line=dict(color="#9333EA", width=2)
            ))

    # White professional chart
    f.update_layout(
        title=dict(
            text=f"{symbol} | Candlestick Chart",
            font=dict(size=18, color="#1E293B"),
            x=0.02
        ),
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=650,
        margin=dict(l=8, r=5, t=60, b=15),
        font=dict(
            family="Arial, sans-serif",
            size=11,
            color="#475569"
        ),
        xaxis=dict(
            rangeslider=dict(visible=False),
            showgrid=True,
            gridcolor="#EEF2F7",
            zeroline=False,
            tickfont=dict(size=10, color="#64748B"),
            fixedrange=False
        ),
        yaxis=dict(
            side="right",
            title=dict(
                text="USDT",
                font=dict(size=10, color="#64748B")
            ),
            tickfont=dict(size=9, color="#64748B"),
            showgrid=True,
            gridcolor="#EEF2F7",
            zeroline=False,
            tickformat="~s",
            fixedrange=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            x=0.01,
            font=dict(size=10, color="#334155")
        ),
        hovermode="x unified",
        dragmode="pan"
    )

    return f
    d = df.tail(count).copy()

    f = go.Figure()

    # Main candlestick chart
    f.add_trace(go.Candlestick(
        x=d["time"],
        open=d["open"],
        high=d["high"],
        low=d["low"],
        close=d["close"],
        name=symbol,
        increasing=dict(
            line=dict(color="#00C087", width=1),
            fillcolor="#00C087"
        ),
        decreasing=dict(
            line=dict(color="#F6465D", width=1),
            fillcolor="#F6465D"
        ),
        whiskerwidth=0.5
    ))

    # Moving averages
    if emas:
        f.add_trace(go.Scatter(
            x=d["time"], y=d["EMA20"],
            name="EMA 20",
            line=dict(color="#F0B90B", width=2)
        ))

        f.add_trace(go.Scatter(
            x=d["time"], y=d["EMA50"],
            name="EMA 50",
            line=dict(color="#3B82F6", width=2)
        ))

        if len(df) >= 200:
            f.add_trace(go.Scatter(
                x=d["time"], y=d["EMA200"],
                name="EMA 200",
                line=dict(color="#A78BFA", width=2)
            ))

    # Professional dark layout
    f.update_layout(
        title=dict(
            text=f"{symbol}  |  {interval_label if False else 'Candlestick Chart'}",
            font=dict(size=20, color="#F1F5F9"),
            x=0.02
        ),
        template="plotly_dark",
        paper_bgcolor="#0B1220",
        plot_bgcolor="#111827",
        height=620,
        margin=dict(l=15, r=15, t=65, b=20),
        font=dict(
            family="Arial, sans-serif",
            size=12,
            color="#CBD5E1"
        ),
        xaxis=dict(
            rangeslider=dict(visible=False),
            showgrid=True,
            gridcolor="rgba(148,163,184,0.12)",
            zeroline=False,
            showline=True,
            linecolor="#334155",
            fixedrange=False
        ),
        yaxis=dict(
            side="right",
            title="Price (USDT)",
            showgrid=True,
            gridcolor="rgba(148,163,184,0.12)",
            zeroline=False,
            showline=True,
            linecolor="#334155",
            fixedrange=False,
            tickformat=",.8f"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            x=0.01,
            bgcolor="rgba(0,0,0,0)"
        ),
        hovermode="x unified",
        dragmode="pan"
    )

    return f

    d=df.tail(count)
    f=go.Figure()
    f.add_trace(go.Candlestick(x=d.time,open=d.open,high=d.high,low=d.low,close=d.close,name=symbol,
        increasing=dict(line=dict(color="#00C087"),fillcolor="#00C087"),
        decreasing=dict(line=dict(color="#F6465D"),fillcolor="#F6465D")))
    if emas:
        f.add_trace(go.Scatter(x=d.time,y=d.EMA20,name="EMA 20",line=dict(color="#F0B90B",width=1.7)))
        f.add_trace(go.Scatter(x=d.time,y=d.EMA50,name="EMA 50",line=dict(color="#3B82F6",width=1.7)))
        if len(df)>=200: f.add_trace(go.Scatter(x=d.time,y=d.EMA200,name="EMA 200",line=dict(color="#B084F5",width=1.5)))
    f.update_layout(title=f"{symbol} • Candlestick Chart",template="plotly_dark",paper_bgcolor="#0B1220",plot_bgcolor="#0B1220",
        height=520,margin=dict(l=8,r=8,t=50,b=8),xaxis=dict(rangeslider_visible=False,showgrid=True,gridcolor="rgba(140,160,180,.12)"),
        yaxis=dict(side="right",title="Price (USDT)",showgrid=True,gridcolor="rgba(140,160,180,.12)"),
        legend=dict(orientation="h",y=1.02,x=.01),hovermode="x unified",dragmode="pan")
    return f

def market_signal(d):
    last,prev=d.iloc[-1],d.iloc[-2]
    if last.EMA20>last.EMA50 and last.close>last.EMA20 and last.RSI<70: trend="مثبت رجحان"
    elif last.EMA20<last.EMA50 and last.close<last.EMA20 and last.RSI>30: trend="کمزور / منفی رجحان"
    else: trend="ملا جلا رجحان"
    if prev.EMA20<=prev.EMA50 and last.EMA20>last.EMA50: sig="EMA کراس اوور اوپر"
    elif prev.EMA20>=prev.EMA50 and last.EMA20<last.EMA50: sig="EMA کراس اوور نیچے"
    else: sig="نیا EMA کراس اوور نہیں"
    return trend,sig

@st.cache_data(ttl=300, show_spinner=False)
def news_feed():
    feeds=[("CoinDesk","https://www.coindesk.com/arc/outboundfeeds/rss/"),("Cointelegraph","https://cointelegraph.com/rss")]
    out=[]
    good=["surge","rally","approval","adoption","bullish","inflow","breakout","growth"]
    bad=["crash","hack","lawsuit","ban","bearish","outflow","liquidation","fraud"]
    for src,url in feeds:
        try:
            root=ET.fromstring(requests.get(url,headers=HEADERS,timeout=8).content)
            for item in root.findall(".//item"):
                title=item.findtext("title",default="").strip()
                link=item.findtext("link",default="").strip()
                date=item.findtext("pubDate",default="")
                text=title.lower()
                p=sum(w in text for w in good); n=sum(w in text for w in bad)
                mood="مثبت الفاظ" if p>n else ("منفی الفاظ" if n>p else "غیر واضح")
                if title: out.append({"ماخذ":src,"خبر":title,"وقت":date,"اندازہ":mood,"لنک":link})
        except Exception: pass
    return pd.DataFrame(out).drop_duplicates(subset=["خبر"]) if out else pd.DataFrame()

symbols=["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","LTCUSDT","TRXUSDT","TONUSDT"]
if "watchlist" not in st.session_state: st.session_state.watchlist=["BTCUSDT","ETHUSDT","SOLUSDT"]
if "alerts" not in st.session_state: st.session_state.alerts=[]
if "paper_balance" not in st.session_state: st.session_state.paper_balance=10000.0
if "paper_trades" not in st.session_state: st.session_state.paper_trades=[]

st.sidebar.title("₿ Crypto AI Pro+")
symbol=st.sidebar.selectbox("مارکیٹ منتخب کریں",symbols)
interval=st.sidebar.selectbox("ٹائم فریم",["1m","5m","15m","30m","1h","4h","1d"],index=2)
count=st.sidebar.select_slider("چارٹ پر کینڈلز",options=[50,75,100,150,200,300],value=100)
emas=st.sidebar.checkbox("EMA لائنیں دکھائیں",True)
if st.sidebar.button("🔄 ڈیٹا ریفریش کریں"):
    st.cache_data.clear(); st.rerun()
st.sidebar.info("یہ تعلیمی ڈیش بورڈ ہے۔ حقیقی ٹریڈ نہیں کرتا اور منافع کی ضمانت نہیں دیتا۔")

st.title("₿ CRYPTO AI DASHBOARD PRO+")
st.caption("لائیو مارکیٹ • خوبصورت چارٹ • اردو مارکیٹ اسسٹنٹ • خبریں • رسک مینیجر")
st.write("صفحہ اپ ڈیٹ:",datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
with st.spinner("مارکیٹ ڈیٹا لوڈ ہو رہا ہے..."):
    df=candles(symbol,interval); tick=ticker(symbol)
has=not df.empty
if has:
    last=df.iloc[-1]; price=float(last.close)
    change=float(tick.get("priceChangePercent",0)) if tick else 0
    vol=float(tick.get("quoteVolume",0)) if tick else 0
    trend,sig=market_signal(df)
    a,b,c,d,e=st.columns(5)
    a.metric("قیمت",money(price),f"{change:.2f}% / 24h")
    b.metric("24h حجم",f"${vol:,.0f}")
    c.metric("RSI 14",f"{last.RSI:.1f}")
    d.metric("رجحان",trend)
    e.metric("تکنیکی اشارہ",sig)
else:
    st.error("مارکیٹ ڈیٹا فی الحال نہیں ملا۔ ریفریش کریں یا کچھ دیر بعد کوشش کریں۔ دوسرے ٹیبز پھر بھی استعمال کیے جا سکتے ہیں۔")
    price=0; change=0; trend="ڈیٹا نہیں"; sig="ڈیٹا نہیں"; last=None

tabs=st.tabs(["📊 چارٹ","🤖 اردو اسسٹنٹ","📰 خبریں","🔔 الرٹس/واچ لسٹ","🧪 پیپر ٹریڈنگ","🧠 رسک مینیجر","📈 فیوچرز","☕ مدد"])
with tabs[0]:
    st.subheader(f"{symbol} — {interval}")
    if has:
        st.plotly_chart(chart(df,symbol,count,emas),width="stretch",
            config={
"scrollZoom": True,
"displaylogo": False,
"responsive": True,
"doubleClick": "reset",
"modeBarButtonsToAdd": ["zoom2d", "pan2d", "resetScale2d"],
"displayModeBar": True,
"showTips": True
}
        st.markdown("### تازہ کینڈلز")
        st.dataframe(df[["time","open","high","low","close","volume","EMA20","EMA50","RSI"]].tail(20).sort_values("time",ascending=False),width="stretch",hide_index=True)
        v=df.tail(100); vf=go.Figure()
        vf.add_trace(go.Bar(x=v.time,y=v.volume,name="Volume"))
        vf.add_trace(go.Scatter(x=v.time,y=v.VolumeMA20,name="20 candle average"))
        vf.update_layout(template="plotly_dark",height=300,title="ٹریڈ کا حجم")
        st.plotly_chart(vf,width="stretch")
    else: st.info("ڈیٹا دستیاب ہوتے ہی چارٹ یہاں نظر آئے گا۔")

with tabs[1]:
    st.subheader("🤖 مفت اردو مارکیٹ اسسٹنٹ")
    st.caption("یہ rule-based مددگار ہے، حقیقی ChatGPT/LLM نہیں اور اس کے لیے paid API نہیں چاہیے۔")
    if has:
        rsi=float(last.RSI)
        rtxt="RSI زیادہ ہے؛ قیمت میں واپسی کا خطرہ ہو سکتا ہے۔" if rsi>=70 else ("RSI کم ہے؛ فروخت کا دباؤ بڑھا ہو سکتا ہے۔" if rsi<=30 else "RSI درمیانی حد میں ہے۔")
        etxt="EMA 20، EMA 50 سے اوپر ہے۔" if last.EMA20>last.EMA50 else "EMA 20، EMA 50 سے نیچے ہے۔"
        vtxt="حجم 20 کینڈلز کی اوسط سے زیادہ ہے۔" if pd.notna(last.VolumeMA20) and last.volume>last.VolumeMA20 else "حجم 20 کینڈلز کی اوسط سے زیادہ نہیں۔"
        st.markdown(f"""### مارکیٹ رپورٹ
**اثاثہ:** {symbol}  
**قیمت:** {price:,.8f} USDT  
**24 گھنٹے کی تبدیلی:** {change:.2f}%  
**رجحان:** {trend}  
**تکنیکی اشارہ:** {sig}  
**RSI ({rsi:.1f}):** {rtxt}  
**EMA:** {etxt}  
**حجم:** {vtxt}  

**احتیاط:** یہ ماضی اور موجودہ ڈیٹا کی سادہ تشریح ہے، قیمت یا منافع کی ضمانت نہیں۔""")
        q=st.text_input("سوال لکھیں، مثلاً RSI کیا ہے؟",key="urdu_question")
        if st.button("اردو میں جواب دیں"):
            q=q.lower().strip()
            if not q: st.info("پہلے سوال لکھیں۔")
            elif any(w in q for w in ["rsi","آر ایس آئی"]): st.write(f"RSI {rsi:.1f} ہے۔ {rtxt} RSI اکیلا فیصلہ کرنے کے لیے کافی نہیں۔")
            elif any(w in q for w in ["ema","رجحان","ٹرینڈ","trend"]): st.write(f"موجودہ کیفیت: {trend}. {etxt}")
            elif any(w in q for w in ["قیمت","price","کتنی"]): st.write(f"{symbol} کی آخری دستیاب بند قیمت {price:,.8f} USDT ہے۔")
            elif any(w in q for w in ["خرید","بیچ","buy","sell","سگنل","signal"]): st.write(f"رجحان {trend} اور اشارہ {sig} ہے۔ اسے یقینی خرید/فروخت نہ سمجھیں؛ پہلے نقصان کی حد طے کریں۔")
            elif any(w in q for w in ["حجم","volume"]): st.write(vtxt+" حجم اکیلا سمت کی تصدیق نہیں کرتا۔")
            else: st.write("میں فی الحال قیمت، RSI، EMA، حجم اور تکنیکی اشاروں کے سوالات کے جواب دے سکتا ہوں۔")
    else: st.info("مارکیٹ ڈیٹا دستیاب نہیں، اس لیے ابھی لائیو رپورٹ نہیں بن سکتی۔")

with tabs[2]:
    st.subheader("📰 کرپٹو خبریں")
    if st.button("خبریں ریفریش کریں"): news_feed.clear()
    n=news_feed()
    if n.empty: st.warning("خبر فیڈ دستیاب نہیں۔ بعد میں دوبارہ کوشش کریں۔")
    else:
        filt=st.selectbox("فلٹر",["سب","مثبت الفاظ","منفی الفاظ","غیر واضح"])
        n=n if filt=="سب" else n[n["اندازہ"]==filt]
        for _,row in n.head(30).iterrows():
            st.markdown("### "+row["خبر"]); st.caption(f"{row['ماخذ']} • {row['وقت']} • {row['اندازہ']}")
            if isinstance(row["لنک"],str) and row["لنک"].startswith("http"): st.markdown(f"[اصل خبر پڑھیں]({row['لنک']})")
            st.markdown("---")
    st.caption("خبر کا sentiment سادہ لفظی اندازہ ہے، مکمل AI تجزیہ نہیں۔")

with tabs[3]:
    st.subheader("🔔 قیمت الرٹس")
    with st.form("alert_form"):
        ass=st.selectbox("اثاثہ",symbols,key="alert_asset")
        ap=st.number_input("الرٹ قیمت USDT",min_value=0.00000001,value=1000.0,format="%.8f")
        direction=st.radio("کب الرٹ ہو؟",["اوپر یا برابر","نیچے یا برابر"])
        add=st.form_submit_button("الرٹ شامل کریں")
        if add:
            st.session_state.alerts.append({"symbol":ass,"price":float(ap),"direction":direction,"hit":False})
            st.success("الرٹ شامل ہو گیا۔")
    for al in st.session_state.alerts:
        t=ticker(al["symbol"]); cur=float(t["lastPrice"]) if t and t.get("lastPrice") else None
        hit=cur is not None and (cur>=al["price"] if al["direction"]=="اوپر یا برابر" else cur<=al["price"])
        if hit: al["hit"]=True
        st.write(f"{al['symbol']} • حد {money(al['price'])} • موجودہ {money(cur)} • {'ٹرگر' if al['hit'] else 'انتظار'}")
    if st.button("تمام الرٹس ختم کریں"): st.session_state.alerts=[]; st.rerun()
    st.caption("الرٹس صرف ایپ rerun/refresh پر چیک ہوتے ہیں، background mobile notifications نہیں۔")
    st.markdown("### واچ لسٹ")
    ws=st.selectbox("اثاثہ شامل کریں",symbols,key="watch_asset")
    if st.button("واچ لسٹ میں شامل کریں"):
        if ws not in st.session_state.watchlist: st.session_state.watchlist.append(ws)
    rows=[]
    for s in st.session_state.watchlist:
        t=ticker(s)
        if t: rows.append({"اثاثہ":s,"قیمت":money(t.get("lastPrice")),"24h تبدیلی":f"{float(t.get('priceChangePercent',0)):.2f}%"})
    if rows: st.dataframe(pd.DataFrame(rows),width="stretch",hide_index=True)
    if st.button("واچ لسٹ صاف کریں"): st.session_state.watchlist=[]; st.rerun()

with tabs[4]:
    st.subheader("🧪 فرضی ٹریڈنگ")
    st.metric("فرضی بیلنس",f"${st.session_state.paper_balance:,.2f}")
    st.caption("حقیقی آرڈر نہیں لگتا اور حقیقی رقم استعمال نہیں ہوتی۔")
    with st.form("paper"):
        ps=st.selectbox("اثاثہ",symbols,key="paper_asset")
        side=st.radio("عمل",["BUY / خرید","SELL / فروخت"],horizontal=True)
        qty=st.number_input("مقدار",min_value=0.00000001,value=0.001,format="%.8f")
        ep=st.number_input("فرضی قیمت",min_value=0.00000001,value=float(price if has else 1),format="%.8f")
        submit=st.form_submit_button("فرضی ٹریڈ محفوظ کریں")
        if submit:
            total=float(qty)*float(ep)
            if "BUY" in side and total>st.session_state.paper_balance: st.error("فرضی بیلنس کافی نہیں۔")
            else:
                st.session_state.paper_balance += -total if "BUY" in side else total
                st.session_state.paper_trades.append({"وقت":datetime.now(timezone.utc).isoformat(),"اثاثہ":ps,"عمل":side,"مقدار":qty,"قیمت":ep,"کل":total})
                st.success("فرضی ٹریڈ محفوظ ہو گئی۔")
    if st.session_state.paper_trades: st.dataframe(pd.DataFrame(st.session_state.paper_trades),width="stretch",hide_index=True)
    if st.button("پیپر ٹریڈنگ ری سیٹ"): st.session_state.paper_balance=10000.0; st.session_state.paper_trades=[]; st.rerun()

with tabs[5]:
    st.subheader("🧠 رسک مینیجر")
    a,b=st.columns(2)
    with a:
        bal=st.number_input("اکاؤنٹ بیلنس USDT",min_value=1.0,value=1000.0)
        rp=st.number_input("فی ٹریڈ رسک %",min_value=0.1,max_value=10.0,value=1.0,step=0.1)
        entry=st.number_input("انٹری قیمت",min_value=0.00000001,value=float(price if has else 100),format="%.8f")
        stop=st.number_input("اسٹاپ لاس",min_value=0.00000001,value=float(price*.98 if has else 98),format="%.8f")
        target=st.number_input("ٹارگٹ",min_value=0.00000001,value=float(price*1.04 if has else 104),format="%.8f")
    dist=abs(entry-stop); cash=bal*rp/100; size=cash/dist if dist else 0; rr=abs(target-entry)/dist if dist else 0
    with b:
        st.metric("منصوبہ بند رسک",f"${cash:,.2f}"); st.metric("اندازاً مقدار",f"{size:,.6f}"); st.metric("رسک/ریوارڈ",f"1 : {rr:.2f}")
    st.caption("فیس، slippage، leverage اور liquidation شامل نہیں۔ یہ تعلیمی کیلکولیٹر ہے۔")

with tabs[6]:
    st.subheader("📈 فیوچرز ڈیٹا")
    with st.spinner("فیوچرز ڈیٹا لوڈ ہو رہا ہے..."):
        prem=api(f"{FUTURES}/fapi/v1/premiumIndex",{"symbol":symbol})
        oi=api(f"{FUTURES}/fapi/v1/openInterest",{"symbol":symbol})
        ratio=api(f"{FUTURES}/futures/data/globalLongShortAccountRatio",{"symbol":symbol,"period":"5m","limit":1})
    if prem:
        a,b,c=st.columns(3); a.metric("Mark Price",money(prem.get("markPrice")))
        b.metric("Funding Rate",f"{float(prem.get('lastFundingRate',0))*100:.5f}%"); c.metric("Index Price",money(prem.get("indexPrice")))
    if oi: st.metric("Open Interest",oi.get("openInterest","N/A"))
    if isinstance(ratio,list) and ratio:
        row=ratio[0]; a,b,c=st.columns(3); a.metric("Long/Short ratio",row.get("longShortRatio","N/A"))
        b.metric("Long share",f"{float(row.get('longAccount',0))*100:.2f}%"); c.metric("Short share",f"{float(row.get('shortAccount',0))*100:.2f}%")
    if not prem and not oi and not ratio: st.warning("فیوچرز API دستیاب نہیں۔ یہ خطے یا نیٹ ورک کی پابندی ہو سکتی ہے۔")
    st.info("یہ مجموعی مارکیٹ اعدادوشمار ہیں، کسی مخصوص ٹریڈر کی پوزیشن نہیں۔")

with tabs[7]:
    st.subheader("☕ سیکھیں، جلد بازی نہ کریں")
    st.write("کرپٹو مارکیٹ میں ہر لمحہ ٹریڈ ضروری نہیں۔ کبھی انتظار کرنا بھی اچھا فیصلہ ہے۔")
    if st.button("آج کی یاد دہانی"): st.success("اپنے اصولوں پر قائم رہیں، جلد بازی نہ کریں، اور اتنا ہی رسک لیں جسے برداشت کر سکیں۔")
    st.info("یہ ڈیش بورڈ معلومات اور مشق کے لیے ہے، مالی مشورہ نہیں۔")

st.markdown("---")
st.caption("Crypto AI Dashboard Pro+ • Public market data • No real orders • Educational use only")

