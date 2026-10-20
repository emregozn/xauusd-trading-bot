
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

st.title("📈 XAU/USD Trading Dashboard")
st.caption("Altın / ABD Doları • Teknik analiz ve sanal sinyal takibi")

st.warning(
    "Bu uygulama eğitim ve analiz amaçlıdır. "
    "Sinyaller yatırım tavsiyesi değildir. "
    "Gerçek işlem yapmadan önce sanal test ve geçmiş veri testi yapın."
)

# --------------------------------------------------
# VERİ KAYNAĞI VE AYARLAR
# --------------------------------------------------
with st.sidebar:
    st.header("Veri kaynağı")

    mode = st.radio(
        "Çalışma modu",
        ["Twelve Data API", "Demo veri"],
        index=0,
        key="calisma_modu"
    )
        st.write("Seçili kaynak:", mode)
    interval = st.selectbox(
        "Mum aralığı",
        ["1h", "4h", "1day"],
        index=1,
        key="mum_araligi"
    )

    st.divider()
    st.header("Analiz ayarları")

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

score = 0

if ema_f > ema_s:
    score += 1
elif ema_f < ema_s:
    score -= 1

if price > ema_f:
    score += 1
elif price < ema_f:
    score -= 1

if rsi < 30:
    score += 1
elif rsi > 70:
    score -= 1

if score >= 2:
    signal = "AL eğilimi"
elif score <= -2:
    signal = "SAT eğilimi"
else:
    signal = "NÖTR"

# --------------------------------------------------
# ÖZET KUTULARI
# --------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

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

st.caption(
    f"Veri kaynağı: {mode} • "
    f"Mum aralığı: {interval} • "
    f"Son mum: {last_time.strftime('%Y-%m-%d %H:%M UTC')}"
)

# --------------------------------------------------
# GRAFİK
# --------------------------------------------------
st.subheader("XAU/USD Mum Grafiği")

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
        name=f"EMA {ema_fast}"
    )
)

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["EMA_slow"],
        mode="lines",
        name=f"EMA {ema_slow}"
    )
)

fig.update_layout(
    height=600,
    xaxis_rangeslider_visible=False,
    template="plotly_dark",
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(orientation="h")
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# RSI VE ATR
# --------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("RSI")

    rsi_fig = go.Figure()

    rsi_fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["RSI"],
            mode="lines",
            name="RSI"
        )
    )

    rsi_fig.add_hline(y=70, line_dash="dash")
    rsi_fig.add_hline(y=30, line_dash="dash")

    rsi_fig.update_layout(
        height=300,
        yaxis_range=[0, 100],
        template="plotly_dark"
    )

    st.plotly_chart(
        rsi_fig,
        use_container_width=True
    )

with right:
    st.subheader("Volatilite")

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
with st.expander("Son mum verilerini görüntüle"):
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
    "Bu uygulama basit teknik göstergeler kullanır. "
    "Komisyon, spread, kayma ve işlem yürütme koşulları "
    "hesaplanmaz. Tek başına alım-satım kararı için kullanılmamalıdır."
)
