import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="XAU/USD Signal Lab", page_icon="📈", layout="wide")

st.title("XAU/USD Signal Lab")
st.caption("İlk prototip • Karar destek sistemi • Otomatik emir göndermez")

st.warning(
    "Bu prototip yatırım tavsiyesi değildir. Demo modu sentetik veri kullanır; "
    "gerçek veriyle çalışırken bile sinyalleri sanal işlem ve geçmiş testlerle doğrulayın."
)

with st.sidebar:
    st.header("Veri kaynağı")
    mode = st.radio("Çalışma modu", ["Demo veri", "Twelve Data API"], index=0)
    api_key = st.secrets.get("TWELVE_DATA_API_KEY", "")
    if mode == "Twelve Data API":
        api_key = st.text_input(
    "Twelve Data API anahtarı",
    value=api_key,
    type="password"
)
        st.caption("Anahtar bu oturumda kullanılır; koda yazmayın veya paylaşmayın.")
    st.divider()
    st.header("Sinyal ayarları")
    rsi_period = st.slider("RSI periyodu", 7, 21, 14)
    ema_fast = st.slider("Hızlı EMA", 5, 30, 20)
    ema_slow = st.slider("Yavaş EMA", 20, 100, 50)
    buy_threshold = st.slider("AL eşiği", 10, 60, 30)
    strong_threshold = st.slider("GÜÇLÜ AL eşiği", 50, 95, 75)
    st.caption("Bu eşikler başlangıç varsayımlarıdır; optimize edilmiş veya kârlılığı kanıtlanmış değildir.")

def demo_data(n=600, seed=7):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(end=pd.Timestamp.now(tz="UTC").floor("h"), periods=n, freq="h")
    drift = np.linspace(0, 90, n) + 22 * np.sin(np.linspace(0, 14, n))
    returns = rng.normal(0.00005, 0.0038, n)
    close = 2300 + drift + np.cumsum(returns * 2300)
    close = close - close[0] + 2300 + drift
    open_ = np.r_[close[0], close[:-1]]
    spread = rng.uniform(1.0, 8.0, n)
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    volume = rng.integers(100, 1000, n)
    return pd.DataFrame({"datetime": idx, "open": open_, "high": high, "low": low, "close": close, "volume": volume}).set_index("datetime")

def fetch_twelvedata(symbol, interval, outputsize, key):
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": key,
        "timezone": "UTC",
        "format": "JSON",
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") == "error" or "values" not in payload:
        raise ValueError(payload.get("message", "API yanıtında mum verisi bulunamadı."))
    df = pd.DataFrame(payload["values"])
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif col == "volume":
            df[col] = np.nan
    return df.sort_values("datetime").dropna(subset=["open", "high", "low", "close"]).set_index("datetime")

def add_indicators(df, rsi_period, ema_fast, ema_slow):
    x = df.copy()
    close = x["close"]
    x["ema_fast"] = close.ewm(span=ema_fast, adjust=False).mean()
    x["ema_slow"] = close.ewm(span=ema_slow, adjust=False).mean()
    x["ema_200"] = close.ewm(span=200, adjust=False).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/rsi_period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/rsi_period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    x["rsi"] = 100 - (100 / (1 + rs))
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    x["macd"] = ema12 - ema26
    x["macd_signal"] = x["macd"].ewm(span=9, adjust=False).mean()
    prev_close = close.shift(1)
    tr = pd.concat([
        x["high"] - x["low"],
        (x["high"] - prev_close).abs(),
        (x["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    x["atr"] = tr.rolling(14).mean()
    x["bb_mid"] = close.rolling(20).mean()
    std = close.rolling(20).std()
    x["bb_upper"] = x["bb_mid"] + 2 * std
    x["bb_lower"] = x["bb_mid"] - 2 * std
    return x

def score_signal(df):
    row = df.iloc[-1]
    prev = df.iloc[-2]
    score = 0
    reasons = []
    if pd.notna(row["ema_fast"]) and pd.notna(row["ema_slow"]):
        if row["ema_fast"] > row["ema_slow"]:
            score += 25
            reasons.append("Hızlı EMA, yavaş EMA'nın üzerinde: kısa vadeli trend lehine.")
        else:
            score -= 25
            reasons.append("Hızlı EMA, yavaş EMA'nın altında: kısa vadeli trend aleyhine.")
    if pd.notna(row["ema_200"]):
        if row["close"] > row["ema_200"]:
            score += 15
            reasons.append("Fiyat EMA 200 üzerinde.")
        else:
            score -= 15
            reasons.append("Fiyat EMA 200 altında.")
    if pd.notna(row["rsi"]):
        if 52 <= row["rsi"] <= 68:
            score += 15
            reasons.append(f"RSI {row['rsi']:.1f}: momentum yükselişi destekliyor, aşırı alım bölgesinde değil.")
        elif row["rsi"] < 45:
            score -= 15
            reasons.append(f"RSI {row['rsi']:.1f}: momentum zayıf.")
        elif row["rsi"] > 75:
            score -= 5
            reasons.append(f"RSI {row['rsi']:.1f}: momentum güçlü olsa da aşırı uzama riski var.")
        else:
            reasons.append(f"RSI {row['rsi']:.1f}: tek başına belirgin yön teyidi vermiyor.")
    if pd.notna(row["macd"]) and pd.notna(row["macd_signal"]):
        if row["macd"] > row["macd_signal"] and row["macd"] >= prev["macd"]:
            score += 15
            reasons.append("MACD sinyal çizgisinin üzerinde ve momentum artıyor.")
        elif row["macd"] < row["macd_signal"] and row["macd"] <= prev["macd"]:
            score -= 15
            reasons.append("MACD sinyal çizgisinin altında ve momentum zayıflıyor.")
    if pd.notna(row["bb_mid"]):
        if row["close"] > row["bb_mid"]:
            score += 10
            reasons.append("Kapanış Bollinger orta bandının üzerinde.")
        else:
            score -= 10
            reasons.append("Kapanış Bollinger orta bandının altında.")
    # Score is intentionally technical-only in v1. No macro/news score until reliable feeds are connected.
    score = int(np.clip(score, -100, 100))
    if score >= 75:
        signal = "GÜÇLÜ AL"
    elif score >= 30:
        signal = "AL"
    elif score <= -75:
        signal = "GÜÇLÜ SAT"
    elif score <= -30:
        signal = "SAT"
    else:
        signal = "BEKLE"
    return score, signal, reasons

try:
    if mode == "Demo veri":
        data = demo_data()
        source_label = "Sentetik demo veri — canlı fiyat değildir"
    elif not api_key:
        st.info("Canlı veriyi almak için sol menüye Twelve Data API anahtarını gir. İstersen demo modunda arayüzü inceleyebilirsin.")
        st.stop()
    else:
        interval = st.selectbox("Mum aralığı", ["1h", "4h", "1day"], index=1)
        data = fetch_twelvedata("XAU/USD", interval, 500, api_key)
        source_label = f"Twelve Data • XAU/USD • {interval}"
except Exception as exc:
    st.error(f"Veri alınamadı: {exc}")
    st.stop()

if len(data) < 210:
    st.warning("EMA 200 ve anlamlı testler için daha fazla geçmiş veri gerekebilir.")

data = add_indicators(data, rsi_period, ema_fast, ema_slow)
score, signal, reasons = score_signal(data)
last = data.iloc[-1]
last_time = data.index[-1]
now_utc = pd.Timestamp.now(tz="UTC")
last_time_utc = pd.Timestamp(last_time)

if last_time_utc.tzinfo is None:
    last_time_utc = last_time_utc.tz_localize("UTC")
else:
    last_time_utc = last_time_utc.tz_convert("UTC")

age_hours = (now_utc - last_time_utc).total_seconds() / 3600

interval = st.session_state.get("interval", "4h")
max_age = {"1h": 3, "4h": 6, "1day": 36}.get(interval, 6)

if mode == "Twelve Data API":
    if age_hours < 0:
        st.error("Veri zamanı geçersiz: zaman damgası gelecekte.")
    elif age_hours > max_age:
        st.error(
            f"VERİ ESKİ: Son mum {age_hours:.1f} saat önce. "
            "Bu veriye dayanarak sinyal değerlendirme."
        )
    else:
        st.success(
            f"Veri zamanı kontrolü geçti • Son mum {age_hours:.1f} saat önce"
        )
st.caption(f"Veri kaynağı: {source_label} • Son mum zamanı: {last_time.strftime('%Y-%m-%d %H:%M UTC')}")
if mode == "Demo veri":
    st.warning("Demo modundasın. Aşağıdaki fiyatlar ve sinyal sentetiktir; işlem kararı için kullanma.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Son kapanış", f"{last['close']:,.2f}")
c2.metric("Teknik puan", f"{score:+d}/100")
c3.metric("Sinyal", signal)
c4.metric("RSI", f"{last['rsi']:.1f}" if pd.notna(last["rsi"]) else "—")

st.subheader("XAU/USD fiyatı ve EMA'lar")
chart = data[["close", "ema_fast", "ema_slow", "ema_200"]].tail(250)
st.line_chart(chart, height=360)

left, right = st.columns([1, 1])
with left:
    st.subheader("Sinyal gerekçeleri")
    for reason in reasons:
        st.write(f"• {reason}")
    st.caption("Bu sürüm yalnızca teknik puan üretir. Makro, haber, COT ve çoklu zaman dilimi teyitleri henüz bağlı değil.")
with right:
    st.subheader("Risk referansları")
    if pd.notna(last["atr"]):
        st.write(f"ATR(14): **{last['atr']:.2f}** fiyat birimi")
        st.write(f"Örnek 1.5 × ATR stop mesafesi: **{1.5 * last['atr']:.2f}**")
        st.write(f"Örnek 3 × ATR hedef mesafesi: **{3 * last['atr']:.2f}**")
        st.caption("Bunlar otomatik işlem önerisi değildir; gerçek stop ve hedefler fiyat yapısı, spread ve risk bütçesiyle doğrulanmalıdır.")
    else:
        st.write("ATR hesaplamak için yeterli veri yok.")

st.subheader("Son mumlar ve göstergeler")
display_cols = ["open", "high", "low", "close", "ema_fast", "ema_slow", "rsi", "macd", "atr"]
st.dataframe(data[display_cols].tail(20).sort_index(ascending=False), use_container_width=True)

st.subheader("İlk sürüm kapsamı")
st.markdown("""
- ✅ Demo veriyle çalışan arayüz
- ✅ Twelve Data API üzerinden XAU/USD mumlarını alma
- ✅ EMA, RSI, MACD, ATR ve Bollinger hesapları
- ✅ Açıklanabilir, basit teknik puan
- ⏳ Günlük/4 saatlik/1 saatlik çoklu zaman dilimi teyidi
- ⏳ Makroekonomik veri ve haber entegrasyonu
- ⏳ Geçmiş test, işlem maliyetleri ve sanal işlem günlüğü
- ⏳ Kullanıcı hesabı, erişim güvenliği ve bildirimler
""")
