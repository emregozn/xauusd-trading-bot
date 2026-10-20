
import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime, timezone

# --------------------------------------------------
# SAYFA AYARLARI
# --------------------------------------------------
st.set_page_config(
    page_title="XAU/USD Trading Dashboard",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
  .stApp { background: radial-gradient(ellipse at top left, #17243b 0%, #0b1220 42%, #080d17 100%); color: #e7edf7; }
  [data-testid="stSidebar"] { background: linear-gradient(180deg, #101a2b 0%, #0b1220 100%); border-right: 1px solid #26344a; }
  [data-testid="stMetric"] { background: linear-gradient(145deg, rgba(25,39,61,.95), rgba(14,24,40,.95)); border: 1px solid #2a3a52; padding: 16px 18px; border-radius: 14px; box-shadow: 0 8px 24px rgba(0,0,0,.16); }
  [data-testid="stMetricLabel"] { color: #c4d2e6 !important; font-weight: 650 !important; }
  [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 750 !important; }
  [data-testid="stMetricDelta"] { color: #d8e5f5 !important; }
  [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color: #d9e4f3; }
  label, [data-testid="stCaptionContainer"] { color: #b6c6dc !important; }
  [data-testid="stSelectbox"] label, [data-testid="stRadio"] label, [data-testid="stSlider"] label { color: #e1eafa !important; }
  .signal-card { padding: 20px; border-radius: 16px; border: 1px solid #40516a; background: linear-gradient(145deg, #17263b, #101a2b); min-height: 170px; }
  .signal-card.buy { border-top: 4px solid #35d39a; }
  .signal-card.sell { border-top: 4px solid #ff647c; }
  .signal-card.neutral { border-top: 4px solid #f3c969; }
  .signal-eyebrow { color: #c0cee2; font-size: 12px; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; }
  .signal-head { font-size: 27px; line-height: 1.2; font-weight: 800; margin: 8px 0 10px; }
  .signal-body { color: #d5e0ef; font-size: 14px; line-height: 1.55; }
  .reason-list { background: #101a2b; border: 1px solid #354760; border-radius: 14px; padding: 16px 18px; }
  .reason-list ul { margin: 8px 0 0 18px; padding: 0; }
  .reason-list li { margin: 7px 0; color: #e0e9f5; }
  .mini-label { color: #b9c9de; font-size: 13px; font-weight: 700; }
  .small-note { color: #b6c6dc; font-size: 12px; line-height: 1.45; }
  h1, h2, h3 { letter-spacing: -0.025em; }
  h1 { color: #f6f8fc; }
  h2, h3 { color: #dbe7f8; }
  div[data-testid="stDataFrame"] { border: 1px solid #28384f; border-radius: 12px; overflow: hidden; }
  div[data-testid="stAlert"] { border-radius: 12px; }
  .hero { padding: 22px 24px; border: 1px solid #2a3b54; border-radius: 18px; background: linear-gradient(110deg, rgba(24,39,62,.96), rgba(13,22,37,.96)); margin-bottom: 18px; }
  .hero-kicker { color: #8ea9ce; font-size: 12px; text-transform: uppercase; letter-spacing: .16em; font-weight: 700; }
  .hero-title { color: #f5f8ff; font-size: 30px; line-height: 1.15; font-weight: 750; margin-top: 7px; }
  .hero-sub { color: #9fb0c9; font-size: 14px; margin-top: 8px; }
  .pill { display: inline-block; border: 1px solid #344a68; background: #15243a; color: #c7d8ef; border-radius: 999px; padding: 5px 10px; margin-right: 6px; font-size: 12px; }
  .section-note { color: #93a6c1; font-size: 13px; }
  hr { border-color: #26364d !important; }
</style>
<div class="hero">
  <div class="hero-kicker">MARKET INTELLIGENCE · XAU/USD</div>
  <div class="hero-title">Gold Trading Dashboard</div>
  <div class="hero-sub">Teknik görünüm, momentum, volatilite ve risk seviyeleri tek ekranda.</div>
  <div style="margin-top:14px"><span class="pill">TEKNİK ANALİZ</span><span class="pill">RİSK YÖNETİMİ</span><span class="pill">SİNYAL TAKİBİ</span></div>
</div>
""", unsafe_allow_html=True)

with st.expander("Kullanım ve risk uyarısı", expanded=False):
    st.write("Bu uygulama eğitim ve analiz amaçlıdır. Sinyaller yatırım tavsiyesi değildir. Gerçek işlem yapmadan önce sanal test ve geçmiş veri testi yapın.")

# --------------------------------------------------
# VERİ KAYNAĞI VE AYARLAR
# --------------------------------------------------
with st.sidebar:
    st.header("⚙️ Veri kaynağı")

    mode = st.radio(
    "Çalışma modu",
    ["Twelve Data API", "Demo veri"],
    index=0,
    key="calisma_modu",
)
    st.write("Seçili kaynak:", mode)
    interval = st.selectbox(
        "Mum aralığı",
        ["1h", "4h", "1day"],
        index=1,
        key="mum_araligi"
    )

    st.divider()
    st.header("📐 Analiz ayarları")

    rsi_period = st.slider(
        "RSI periyodu",
        min_value=7,
        max_value=21,
        value=14
    )

    ema_fast = st.selectbox(
        "Hızlı EMA",
        [9, 12, 20],
        index=0
    )

    ema_slow = st.selectbox(
        "Yavaş EMA",
        [21, 26, 50],
        index=1
    )

    st.caption("API anahtarı Streamlit Secrets üzerinden okunur.")

# --------------------------------------------------
# VERİ ÇEKME
# --------------------------------------------------
@st.cache_data(ttl=60)
def get_live_data(api_key, interval):
    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": "XAU/USD",
        "interval": interval,
        "outputsize": 200,
        "apikey": api_key,
        "format": "JSON"
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )
    response.raise_for_status()
    result = response.json()

    if "values" not in result:
        message = result.get(
            "message",
            result.get("code", "Bilinmeyen API hatası")
        )
        raise ValueError(str(message))
    
    
    data = pd.DataFrame(result["values"])
    
    
    if data.empty:
        raise ValueError("API boş veri döndürdü.")

    data["datetime"] = pd.to_datetime(
        data["datetime"],
        utc=True,
        errors="coerce"
    )

    for col in ["open", "high", "low", "close"]:
        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        )

    if "volume" in data.columns:
        data["volume"] = pd.to_numeric(
            data["volume"],
            errors="coerce"
        )

    data = data.dropna(
        subset=["datetime", "open", "high", "low", "close"]
    )

    data = data.sort_values("datetime")
    data = data.drop_duplicates("datetime")
    data = data.set_index("datetime")

    if len(data) < 55:
        raise ValueError(
            "Analiz için yeterli mum verisi gelmedi."
        )

    return data


def get_demo_data(interval):
    seed = 42
    rng = np.random.default_rng(seed)

    periods = 250

    if interval == "1h":
        freq = "h"
    elif interval == "4h":
        freq = "4h"
    else:
        freq = "D"

    end = pd.Timestamp.now(tz="UTC").floor("h")
    dates = pd.date_range(
        end=end,
        periods=periods,
        freq=freq
    )

    changes = rng.normal(0, 8, periods)
    close = 2300 + np.cumsum(changes)
    open_price = np.r_[close[0], close[:-1]]

    high = np.maximum(open_price, close) + rng.uniform(
        1, 8, periods
    )
    low = np.minimum(open_price, close) - rng.uniform(
        1, 8, periods
    )

    data = pd.DataFrame(
        {
            "open": open_price,
            "high": high,
            "low": low,
            "close": close
        },
        index=dates
    )

    return data


# --------------------------------------------------
# TEKNİK GÖSTERGELER
# --------------------------------------------------
def add_indicators(data, rsi_period, ema_fast, ema_slow):
    data = data.copy()

    close = data["close"]
    high = data["high"]
    low = data["low"]

    data["EMA_fast"] = close.ewm(
        span=ema_fast,
        adjust=False
    ).mean()

    data["EMA_slow"] = close.ewm(
        span=ema_slow,
        adjust=False
    ).mean()

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / rsi_period,
        min_periods=rsi_period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / rsi_period,
        min_periods=rsi_period,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    data["RSI"] = 100 - (100 / (1 + rs))

    data["RSI"] = data["RSI"].fillna(50)

    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs()
        ],
        axis=1
    ).max(axis=1)

    data["ATR"] = true_range.rolling(14).mean()

    data["Volume"] = (
        data["volume"]
        if "volume" in data.columns
        else np.nan
    )

    return data


# --------------------------------------------------
# VERİYİ YÜKLE
# --------------------------------------------------
data = None
data_error = None

if mode == "Twelve Data API":
    api_key = st.secrets.get("TWELVE_DATA_API_KEY", "")

    if not api_key:
        st.error(
            "API anahtarı bulunamadı. "
            "Streamlit uygulamasının Secrets bölümünü kontrol et."
        )
        st.stop()

    try:
        with st.spinner("Gerçek piyasa verisi alınıyor..."):
            data = get_live_data(api_key, interval)

    except Exception as exc:
        st.error(f"Veri alınamadı: {exc}")
        st.info(
            "API limitini, XAU/USD sembolünü ve Secrets ayarını kontrol et."
        )
        st.stop()

else:
    data = get_demo_data(interval)
    st.info(
        "Demo modu açık. Bu fiyatlar gerçek piyasa verisi değildir."
    )

# --------------------------------------------------
# VERİ KONTROLÜ
# --------------------------------------------------
if data is None or data.empty:
    st.error("Gösterilecek veri bulunamadı.")
    st.stop()


last_time = data.index[-1]
now_utc = pd.Timestamp.now(tz="UTC")

if last_time.tzinfo is None:
    last_time = last_time.tz_localize("UTC")
else:
    last_time = last_time.tz_convert("UTC")

age_hours = (now_utc - last_time).total_seconds() / 3600

max_age = {
    "1h": 3,
    "4h": 6,
    "1day": 36
}.get(interval, 6)



if mode == "Twelve Data API":
    st.caption(
        f"API mum zamanı: {last_time.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
        f"Şu an UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
        f"Fark: {age_hours:.2f} saat"
    )

    if age_hours < -0.1:
        st.error(
            "API mum zamanı gelecekte görünüyor. "
            "Saat bilgisi doğrulanmadan sinyali kullanma."
        )
    elif age_hours > max_age:
        st.error(
            f"Veri eski: Son mum {age_hours:.1f} saat önce."
        )
    else:
        st.success(
            f"Veri güncellik kontrolü geçti: {age_hours:.1f} saat."
        )


# --------------------------------------------------
# ANALİZ
# --------------------------------------------------
data = add_indicators(
    data,
    rsi_period,
    ema_fast,
    ema_slow
)

last = data.iloc[-1]
previous = data.iloc[-2]

price = float(last["close"])
rsi = float(last["RSI"])
atr = last["ATR"]
ema_f = float(last["EMA_fast"])
ema_s = float(last["EMA_slow"])

# Sinyal bileşenleri: trend, fiyat konumu ve RSI momentumu.
# RSI'nin yalnızca 30 altı / 70 üstü olması tek başına yön sinyali sayılmaz.
prev_rsi = float(previous["RSI"])

trend_up = ema_f > ema_s
trend_down = ema_f < ema_s
price_above_fast = price > ema_f
price_below_fast = price < ema_f
rsi_rising = rsi > prev_rsi
rsi_falling = rsi < prev_rsi

score = 0
if trend_up:
    score += 1
elif trend_down:
    score -= 1

if price_above_fast:
    score += 1
elif price_below_fast:
    score -= 1

# Momentum katkısı için RSI yönü ve aşırı bölge birlikte değerlendirilir.
if rsi_rising and 40 <= rsi <= 70:
    score += 1
elif rsi_falling and 30 <= rsi <= 60:
    score -= 1

if score >= 2:
    signal = "AL eğilimi"
elif score <= -2:
    signal = "SAT eğilimi"
else:
    signal = "NÖTR"

# Kullanıcıya kararın hangi koşullardan geldiğini açıkla.
analysis_rows = [
    {
        "Kriter": "Trend (EMA)",
        "Durum": "Yükseliş" if trend_up else ("Düşüş" if trend_down else "Nötr"),
        "Yorum": f"EMA {ema_fast}: ${ema_f:,.2f} | EMA {ema_slow}: ${ema_s:,.2f}",
    },
    {
        "Kriter": "Fiyat konumu",
        "Durum": "Hızlı EMA üzerinde" if price_above_fast else ("Hızlı EMA altında" if price_below_fast else "EMA ile aynı"),
        "Yorum": f"Kapanış: ${price:,.2f}",
    },
    {
        "Kriter": "RSI momentumu",
        "Durum": "Yükseliyor" if rsi_rising else ("Düşüyor" if rsi_falling else "Değişmedi"),
        "Yorum": f"RSI: {rsi:.1f} | Önceki: {prev_rsi:.1f}",
    },
]

# Görsel özet için her kriterin hangi yönü desteklediğini say.
# Yüzdeler olasılık veya yatırım tavsiyesi değil, üç teknik kriterin uyum oranıdır.
buy_reasons = []
sell_reasons = []
neutral_reasons = []

if trend_up:
    buy_reasons.append(f"EMA {ema_fast}, EMA {ema_slow} üzerinde: kısa vadeli trend yukarı.")
elif trend_down:
    sell_reasons.append(f"EMA {ema_fast}, EMA {ema_slow} altında: kısa vadeli trend aşağı.")
else:
    neutral_reasons.append("EMA'lar birbirine yakın; trend ayrımı zayıf.")

if price_above_fast:
    buy_reasons.append("Son kapanış hızlı EMA'nın üzerinde.")
elif price_below_fast:
    sell_reasons.append("Son kapanış hızlı EMA'nın altında.")
else:
    neutral_reasons.append("Fiyat hızlı EMA çevresinde.")

if rsi_rising and 40 <= rsi <= 70:
    buy_reasons.append(f"RSI {rsi:.1f}: momentum yükseliyor ve aşırı alım bölgesinde değil.")
elif rsi_falling and 30 <= rsi <= 60:
    sell_reasons.append(f"RSI {rsi:.1f}: momentum aşağı yönlü.")
elif rsi >= 70:
    neutral_reasons.append(f"RSI {rsi:.1f}: yüksek momentum var; yeni girişte geri çekilme riski olabilir.")
elif rsi <= 30:
    neutral_reasons.append(f"RSI {rsi:.1f}: zayıf/aşırı satım bölgesi; tek başına AL sinyali değildir.")
else:
    neutral_reasons.append(f"RSI {rsi:.1f}: momentum filtresi net yön desteği vermiyor.")

buy_support = len(buy_reasons)
sell_support = len(sell_reasons)
buy_pct = round(buy_support / 3 * 100)
sell_pct = round(sell_support / 3 * 100)

# --------------------------------------------------
# RİSK / HEDEF SEVİYELERİ (ATR TABANLI)
# --------------------------------------------------
# Bu seviyeler analiz amaçlıdır; işlem emri göndermez.
risk_multiple = 1.5
risk_levels = None

if pd.notna(atr) and float(atr) > 0:
    entry_price = price
    risk_distance = float(atr) * risk_multiple

    if signal == "AL eğilimi":
        risk_levels = {
            "Yön": "AL",
            "Giriş referansı": entry_price,
            "Stop-loss": entry_price - risk_distance,
            "Hedef 1 (1:1)": entry_price + risk_distance,
            "Hedef 2 (1:2)": entry_price + (2 * risk_distance),
            "Hedef 3 (1:3)": entry_price + (3 * risk_distance),
            "Risk mesafesi": risk_distance,
        }
    elif signal == "SAT eğilimi":
        risk_levels = {
            "Yön": "SAT",
            "Giriş referansı": entry_price,
            "Stop-loss": entry_price + risk_distance,
            "Hedef 1 (1:1)": entry_price - risk_distance,
            "Hedef 2 (1:2)": entry_price - (2 * risk_distance),
            "Hedef 3 (1:3)": entry_price - (3 * risk_distance),
            "Risk mesafesi": risk_distance,
        }

# --------------------------------------------------
# DASHBOARD ÖZETİ
# --------------------------------------------------
st.markdown("### Piyasa özeti")
st.caption(f"Kaynak: {mode}  ·  Zaman dilimi: {interval}  ·  Son mum: {last_time.strftime('%Y-%m-%d %H:%M UTC')}")

# --------------------------------------------------
# ÖZET KUTULARI
# --------------------------------------------------
c1, c2, c3, c4 = st.columns(4, gap="medium")

c1.metric(
    "Son kapanış",
    f"${price:,.2f}",
    f"{price - float(previous['close']):+.2f}"
)

c2.metric(
    "RSI",
    f"{rsi:.1f}"
)

c3.metric(
    "Sinyal puanı",
    f"{score:+d} / 3"
)

c4.metric(
    "Teknik görünüm",
    signal
)

st.subheader("Sinyal analizi")
st.caption("Yön desteği yüzdeleri, 3 teknik kriterden kaçının aynı yönü desteklediğini gösterir; kazanma olasılığı değildir.")

if signal == "AL eğilimi":
    card_class, signal_color = "buy", "#56e0ad"
elif signal == "SAT eğilimi":
    card_class, signal_color = "sell", "#ff8193"
else:
    card_class, signal_color = "neutral", "#f3d27c"

signal_cols = st.columns([1.05, 1.5], gap="large")
with signal_cols[0]:
    st.markdown(
        f'<div class="signal-card {card_class}">'
        f'<div class="signal-eyebrow">Mevcut teknik görünüm</div>'
        f'<div class="signal-head" style="color:{signal_color}">{signal}</div>'
        f'<div class="signal-body">Sinyal puanı: <b>{score:+d} / 3</b><br>Son kapanış: <b>${price:,.2f}</b><br>RSI: <b>{rsi:.1f}</b></div>'
        f'</div>',
        unsafe_allow_html=True
    )
with signal_cols[1]:
    st.markdown('<div class="mini-label">Teknik kriterlerin yön uyumu</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mini-label" style="color:#56e0ad">AL yönü desteği · {buy_pct}% ({buy_support}/3 kriter)</div>', unsafe_allow_html=True)
    st.progress(buy_pct / 100)
    st.markdown(f'<div class="mini-label" style="color:#ff8193">SAT yönü desteği · {sell_pct}% ({sell_support}/3 kriter)</div>', unsafe_allow_html=True)
    st.progress(sell_pct / 100)
    st.markdown('<div class="small-note">Bu göstergeler istatistiksel başarı ihtimali değildir; yalnızca mevcut kurallarla uyumu özetler.</div>', unsafe_allow_html=True)

reason_cols = st.columns(2, gap="large")
with reason_cols[0]:
    st.markdown('<div class="reason-list"><b style="color:#56e0ad">🟢 AL yönünü destekleyenler</b><ul>' + ''.join(f'<li>{r}</li>' for r in buy_reasons) + ('' if buy_reasons else '<li>Şu anda AL yönünü destekleyen net kriter yok.</li>') + '</ul></div>', unsafe_allow_html=True)
with reason_cols[1]:
    st.markdown('<div class="reason-list"><b style="color:#ff8193">🔴 SAT yönünü destekleyenler</b><ul>' + ''.join(f'<li>{r}</li>' for r in sell_reasons) + ('' if sell_reasons else '<li>Şu anda SAT yönünü destekleyen net kriter yok.</li>') + '</ul></div>', unsafe_allow_html=True)

with st.expander("Nötr kalan / dikkat edilmesi gereken noktalar"):
    for reason in neutral_reasons:
        st.markdown(f"- {reason}")

if signal == "AL eğilimi":
    st.success("En az iki teknik kriter AL yönünü destekliyor. Bu bir emir değildir; risk ve veri kalitesi ayrıca değerlendirilmelidir.")
elif signal == "SAT eğilimi":
    st.error("En az iki teknik kriter SAT yönünü destekliyor. Bu bir emir değildir; risk ve veri kalitesi ayrıca değerlendirilmelidir.")
else:
    st.warning("Teknik kriterler aynı yönde yeterince birleşmiyor; sistem NÖTR kalıyor.")

st.subheader("Risk yönetimi ve kâr hedefleri")
if risk_levels is None:
    st.info(
        "ATR henüz hesaplanamadı veya sinyal nötr. "
        "Bu nedenle yönlü stop-loss/kâr hedefi gösterilmiyor."
    )
else:
    st.caption(
        f"Referans giriş: son kapanış • Stop mesafesi: {risk_multiple:.1f} × ATR(14) "
        "• Seviyeler otomatik işlem emri değildir."
    )
    risk_cols = st.columns(5, gap="small")
    risk_cols[0].metric("Giriş referansı", f"${risk_levels['Giriş referansı']:,.2f}")
    risk_cols[1].metric("Stop-loss", f"${risk_levels['Stop-loss']:,.2f}")
    risk_cols[2].metric("Hedef 1 (1:1)", f"${risk_levels['Hedef 1 (1:1)']:,.2f}")
    risk_cols[3].metric("Hedef 2 (1:2)", f"${risk_levels['Hedef 2 (1:2)']:,.2f}")
    risk_cols[4].metric("Hedef 3 (1:3)", f"${risk_levels['Hedef 3 (1:3)']:,.2f}")

st.caption(
    f"Veri kaynağı: {mode} • "
    f"Mum aralığı: {interval} • "
    f"Son mum: {last_time.strftime('%Y-%m-%d %H:%M UTC')}"
)

# --------------------------------------------------
# GRAFİK
# --------------------------------------------------
st.subheader("Fiyat grafiği")
st.caption("Mumlar ve EMA çizgileri · Grafiği yakınlaştırmak için sürükleyin, varsayılan görünüme dönmek için çift tıklayın.")

fig = go.Figure()

fig.add_trace(
    go.Candlestick(
        x=data.index,
        open=data["open"],
        high=data["high"],
        low=data["low"],
        close=data["close"],
        name="XAU/USD"
    )
)

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["EMA_fast"],
        mode="lines",
        name=f"EMA {ema_fast}",
        line=dict(color="#42d6a4", width=2)
    )
)

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["EMA_slow"],
        mode="lines",
        name=f"EMA {ema_slow}",
        line=dict(color="#ffbf69", width=2)
    )
)

fig.update_layout(
    height=580,
    xaxis_rangeslider_visible=False,
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(11,18,32,0.55)",
    margin=dict(l=12, r=12, t=36, b=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    font=dict(color="#c8d5e8"),
    xaxis=dict(gridcolor="rgba(120,145,180,0.12)", zerolinecolor="rgba(120,145,180,0.15)"),
    yaxis=dict(gridcolor="rgba(120,145,180,0.12)", zerolinecolor="rgba(120,145,180,0.15)"),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# RSI VE ATR
# --------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("RSI · Momentum")

    rsi_fig = go.Figure()

    rsi_fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["RSI"],
            mode="lines",
            name="RSI",
            line=dict(color="#7eb6ff", width=2)
        )
    )

    rsi_fig.add_hline(y=70, line_dash="dash")
    rsi_fig.add_hline(y=30, line_dash="dash")

    rsi_fig.update_layout(
        height=300,
        yaxis_range=[0, 100],
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(11,18,32,0.55)",
        margin=dict(l=10, r=10, t=20, b=10),
        font=dict(color="#c8d5e8"),
        xaxis=dict(gridcolor="rgba(120,145,180,0.12)"),
        yaxis=dict(gridcolor="rgba(120,145,180,0.12)")
    )

    st.plotly_chart(
        rsi_fig,
        use_container_width=True
    )

with right:
    st.subheader("Volatilite · ATR")

    if pd.notna(atr):
        st.metric("ATR (14)", f"${float(atr):.2f}")
        st.caption(
            "ATR fiyatın olası hareket genişliğini ölçer; "
            "yön tahmini değildir."
        )
    else:
        st.info("ATR hesaplamak için yeterli veri yok.")

# --------------------------------------------------
# SON MUM VERİLERİ
# --------------------------------------------------
with st.expander("Ham veriler · Son 20 mum"):
    display_cols = [
        "open",
        "high",
        "low",
        "close",
        "EMA_fast",
        "EMA_slow",
        "RSI",
        "ATR"
    ]

    st.dataframe(
        data[display_cols].tail(20).sort_index(
            ascending=False
        ),
        use_container_width=True
    )

st.divider()

st.caption(
    "Bilgilendirme: Bu uygulama basit teknik göstergeler kullanır. Komisyon, spread, kayma ve işlem yürütme koşulları hesaplanmaz. Tek başına alım-satım kararı için kullanılmamalıdır."
)
