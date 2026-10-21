
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
    page_title="Market Intelligence Dashboard",
    page_icon="📈",
    layout="wide"
)

# Uygulama içi bölüm seçimi: yeni tarayıcı sekmesi açmaz.
with st.sidebar:
    st.markdown("## 🧭 Piyasa seçimi")
    market_page = st.radio(
        "Analiz alanı",
        ["🥇 XAU/USD · Altın", "🇹🇷 BIST · Hisseler"],
        index=0,
        key="market_page_selector",
    )

if market_page == "🇹🇷 BIST · Hisseler":
    import concurrent.futures
    from datetime import timedelta

    st.markdown("""
    <style>
      .stApp { background: radial-gradient(ellipse at top left, #17243b 0%, #0b1220 42%, #080d17 100%); color: #e7edf7; }
      [data-testid="stSidebar"] { background: linear-gradient(180deg, #101a2b 0%, #0b1220 100%); border-right: 1px solid #26344a; }
      [data-testid="stMetric"] { background: linear-gradient(145deg, rgba(25,39,61,.95), rgba(14,24,40,.95)); border: 1px solid #2a3a52; padding: 14px; border-radius: 14px; }
      [data-testid="stMetricLabel"] { color: #c4d2e6 !important; }
      [data-testid="stMetricValue"] { color: #fff !important; }
      h1,h2,h3 { color: #f1f5fb; }
    </style>
    <div style="padding:22px 24px;border:1px solid #2a3b54;border-radius:18px;background:linear-gradient(110deg,rgba(24,39,62,.96),rgba(13,22,37,.96));margin-bottom:18px">
      <div style="color:#8ea9ce;font-size:12px;letter-spacing:.16em;font-weight:700">MARKET INTELLIGENCE · BORSA İSTANBUL</div>
      <div style="color:#f5f8ff;font-size:30px;font-weight:750;margin-top:7px">BIST Hisse Analiz Merkezi</div>
      <div style="color:#9fb0c9;font-size:14px;margin-top:8px">Fiyat hareketi, hacim, teknik görünüm ve şirket profili tek ekranda.</div>
    </div>
    """, unsafe_allow_html=True)

    # Geniş tarama evreni. Endeks üyelikleri dönemsel değiştiğinden bu listeler
    # resmi ve eksiksiz endeks bileşenleri olarak değil, düzenlenebilir tarama sepetleri olarak sunulur.
    BIST_WATCHLIST = {
        "AEFES": "Anadolu Efes · İçecek", "AGHOL": "Anadolu Grubu Holding · Holding",
        "AKBNK": "Akbank · Bankacılık", "AKSA": "Aksa · Kimya ve elyaf", "AKSEN": "Aksa Enerji · Enerji",
        "ALARK": "Alarko Holding · Holding/enerji", "ANHYT": "Anadolu Hayat Emeklilik · Sigorta",
        "ARCLK": "Arçelik · Dayanıklı tüketim", "ASELS": "Aselsan · Savunma ve elektronik",
        "ASTOR": "Astor Enerji · Enerji ekipmanları", "AYGAZ": "Aygaz · Enerji dağıtımı",
        "BIMAS": "BİM · Perakende", "BRISA": "Brisa · Lastik", "CCOLA": "Coca-Cola İçecek · İçecek",
        "CIMSA": "Çimsa · Çimento", "DOAS": "Doğuş Otomotiv · Otomotiv", "DOHOL": "Doğan Holding · Holding",
        "ECILC": "Eczacıbaşı İlaç · Sağlık", "EGEEN": "Ege Endüstri · Otomotiv yan sanayi",
        "EKGYO": "Emlak Konut GYO · Gayrimenkul", "ENJSA": "Enerjisa · Elektrik",
        "ENKAI": "Enka İnşaat · İnşaat ve enerji", "EREGL": "Ereğli Demir Çelik · Çelik",
        "FROTO": "Ford Otosan · Otomotiv", "GARAN": "Garanti BBVA · Bankacılık",
        "GESAN": "Girişim Elektrik · Enerji ekipmanları", "GUBRF": "Gübre Fabrikaları · Gübre",
        "HALKB": "Halkbank · Bankacılık", "ISCTR": "İş Bankası C · Bankacılık",
        "ISDMR": "İskenderun Demir Çelik · Çelik", "KARSN": "Karsan · Ticari araçlar",
        "KCHOL": "Koç Holding · Holding", "KONTR": "Kontrolmatik · Enerji teknolojileri",
        "KONYA": "Konya Çimento · Çimento", "KOZAA": "Koza Anadolu Metal · Madencilik",
        "KOZAL": "Koza Altın · Madencilik", "KRDMD": "Kardemir D · Demir çelik",
        "MAVI": "Mavi Giyim · Perakende", "MGROS": "Migros · Perakende", "MIATK": "Mia Teknoloji · Teknoloji",
        "ODAS": "Odaş Elektrik · Enerji", "OTKAR": "Otokar · Savunma ve ticari araç",
        "OYAKC": "Oyak Çimento · Çimento", "PASEU": "Pasifik Eurasia · Lojistik",
        "PETKM": "Petkim · Petrokimya", "PGSUS": "Pegasus · Havacılık", "SAHOL": "Sabancı Holding · Holding",
        "SASA": "SASA · Polyester ve kimya", "SISE": "Şişecam · Cam ve kimyasallar",
        "SOKM": "Şok Marketler · Perakende", "TAVHL": "TAV Havalimanları · Havalimanı işletmeciliği",
        "TCELL": "Turkcell · Telekomünikasyon", "THYAO": "Türk Hava Yolları · Havacılık",
        "TKFEN": "Tekfen Holding · İnşaat ve tarım", "TOASO": "Tofaş · Otomotiv",
        "TRMET": "TR Anadolu Metal Madencilik · Madencilik", "TTKOM": "Türk Telekom · Telekomünikasyon",
        "TTRAK": "Türk Traktör · Tarım makineleri", "TUPRS": "Tüpraş · Rafineri",
        "TURSG": "Türkiye Sigorta · Sigorta", "ULKER": "Ülker · Gıda", "VAKBN": "VakıfBank · Bankacılık",
        "VESBE": "Vestel Beyaz Eşya · Dayanıklı tüketim", "VESTL": "Vestel · Elektronik",
        "YKBNK": "Yapı Kredi · Bankacılık", "ZOREN": "Zorlu Enerji · Enerji",
        "AKFGY": "Akfen GYO · Gayrimenkul", "AKFYE": "Akfen Yenilenebilir Enerji · Enerji",
        "ALBRK": "Albaraka Türk · Bankacılık", "ALFAS": "Alfa Solar Enerji · Güneş enerjisi",
        "ANSGR": "Anadolu Sigorta · Sigorta", "ARDYZ": "Ard Grup Bilişim · Yazılım",
        "ATATP": "ATP Yazılım · Yazılım", "BAGFS": "Bagfaş · Gübre", "BANVT": "Banvit · Gıda",
        "BERA": "Bera Holding · Holding", "BIOEN": "Biotrend Enerji · Atık/enerji",
        "BRSAN": "Borusan Boru · Sanayi", "BTCIM": "Batıçim · Çimento", "CWENE": "CW Enerji · Güneş enerjisi",
        "DEVA": "Deva Holding · İlaç", "ECZYT": "Eczacıbaşı Yatırım · Holding", "EFOR": "Efor Yatırım · Yatırım",
        "ENERY": "Enerya Enerji · Doğal gaz", "EUPWR": "Europower Enerji · Enerji ekipmanları",
        "GENIL": "Gen İlaç · İlaç", "GLYHO": "Global Yatırım Holding · Holding", "GWIND": "Galata Wind · Yenilenebilir enerji",
        "HEKTS": "Hektaş · Tarım kimyasalları", "ISGYO": "İş GYO · Gayrimenkul", "KCAER": "Kocaer Çelik · Çelik",
        "KLGYO": "Kiler GYO · Gayrimenkul", "KMPUR": "Kimteks Poliüretan · Kimya", "KORDS": "Kordsa · Kompozit/lastik",
        "KRVGD": "Kervan Gıda · Gıda", "KUYAS": "Kuyas Yatırım · Yatırım", "LOGO": "Logo Yazılım · Yazılım",
        "LILAK": "Lila Kağıt · Kağıt", "MAKIM": "Makim Makina · Makine", "MEDTR": "Meditera · Sağlık ekipmanları",
        "NETAS": "Netaş · Telekom ekipmanları", "NUHCM": "Nuh Çimento · Çimento", "ORGE": "Orge Enerji · Elektrik taahhüt",
        "PENTA": "Penta Teknoloji · Teknoloji dağıtımı", "QUAGR": "Qua Granite · Seramik", "RALYH": "Ral Yatırım Holding · Holding",
        "REEDR": "Reeder Teknoloji · Elektronik", "RYGYO": "Reysaş GYO · Gayrimenkul", "SKBNK": "Şekerbank · Bankacılık",
        "SMRTG": "Smart Güneş Teknolojileri · Güneş enerjisi", "TABGD": "TAB Gıda · Restoran işletmeciliği",
        "TSKB": "TSKB · Kalkınma ve yatırım bankacılığı", "TMSN": "Tümosan · Motor ve traktör",
        "YEOTK": "Yeo Teknoloji · Enerji mühendisliği", "YYLGD": "Yayla Agro · Gıda", "KATMR": "Katmerciler · Savunma araçları",
    }
    BIST30_WATCH = ["AKBNK", "ASELS", "BIMAS", "DOAS", "EKGYO", "ENKAI", "EREGL", "FROTO", "GARAN", "ISCTR", "KCHOL", "MGROS", "PGSUS", "SAHOL", "SISE", "TCELL", "THYAO", "TOASO", "TUPRS", "YKBNK", "ASTOR", "TAVHL", "TTRAK", "TRMET", "PASEU", "ULKER", "VAKBN", "HALKB", "ENJSA", "TURSG"]
    BIST100_WATCH = list(BIST_WATCHLIST.keys())[:100]
    BIST_ALL_WATCH = list(BIST_WATCHLIST.keys())

    @st.cache_data(ttl=300, show_spinner=False)
    def get_yahoo_history(symbol, range_value="3mo", interval_value="1d"):
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.IS"
        response = requests.get(
            url,
            params={"range": range_value, "interval": interval_value, "events": "div,splits"},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=12
        )
        response.raise_for_status()
        payload = response.json().get("chart", {})
        if payload.get("error"):
            raise ValueError(str(payload["error"].get("description", "Yahoo Finance veri hatası")))
        result = (payload.get("result") or [None])[0]
        if not result:
            raise ValueError("Bu sembol için veri bulunamadı.")
        quotes = result.get("indicators", {}).get("quote", [{}])[0]
        timestamps = result.get("timestamp", [])
        frame = pd.DataFrame({
            "datetime": pd.to_datetime(timestamps, unit="s", utc=True),
            "open": quotes.get("open", []), "high": quotes.get("high", []),
            "low": quotes.get("low", []), "close": quotes.get("close", []),
            "volume": quotes.get("volume", []),
        })
        frame = frame.dropna(subset=["datetime", "open", "high", "low", "close"])
        if frame.empty:
            raise ValueError("Geçerli fiyat verisi gelmedi.")
        return frame.sort_values("datetime").drop_duplicates("datetime").set_index("datetime")

    @st.cache_data(ttl=300, show_spinner=False)
    def get_bist_snapshot(symbols_tuple):
        rows = []
        def one(sym):
            try:
                d = get_yahoo_history(sym, "3mo", "1d")
                close = d["close"].astype(float)
                last = float(close.iloc[-1])
                prev = float(close.iloc[-2]) if len(close) > 1 else last
                vol = float(d["volume"].iloc[-1]) if pd.notna(d["volume"].iloc[-1]) else np.nan
                value = last * vol if pd.notna(vol) else np.nan
                return {"Kod": sym, "Son fiyat": last, "Günlük %": (last / prev - 1) * 100 if prev else np.nan,
                        "Hacim": vol, "Yaklaşık işlem değeri": value, "Veri zamanı": d.index[-1],
                        "Veri": "OK"}
            except Exception as exc:
                return {"Kod": sym, "Son fiyat": np.nan, "Günlük %": np.nan, "Hacim": np.nan,
                        "Yaklaşık işlem değeri": np.nan, "Veri zamanı": pd.NaT, "Veri": str(exc)[:100]}
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            rows = list(pool.map(one, symbols_tuple))
        return pd.DataFrame(rows)

    st.subheader("Piyasa evreni ve değerleme taraması")
    universe_choice = st.selectbox("Hangi hisseleri tarayalım?", ["BIST 30 · izleme sepeti", "BIST 100 · geniş izleme sepeti", "BIST geneli · uygulama tarama evreni"], index=2)
    if universe_choice.startswith("BIST 30"):
        universe_symbols = [x for x in BIST30_WATCH if x in BIST_WATCHLIST]
    elif universe_choice.startswith("BIST 100"):
        universe_symbols = [x for x in BIST100_WATCH if x in BIST_WATCHLIST]
    else:
        universe_symbols = BIST_ALL_WATCH
    st.caption("Endeks sepetleri bu uygulamadaki izleme listeleridir; resmî ve eksiksiz endeks üyeliği değildir. Borsa İstanbul endeks üyelikleri dönemsel olarak değişir. Resmî bileşen listeleri ayrı kaynaktan güncellenmelidir.")

    @st.cache_data(ttl=1800, show_spinner=False)
    def get_yahoo_valuation(symbol):
        # Yahoo Finance fundamentals endpoint; bazı sembollerde/veri anlarında erişim reddedilebilir.
        url = f"https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{symbol}.IS"
        params = {"type": "quarterlyMarketCap,quarterlyStockholdersEquity,annualStockholdersEquity,quarterlyTotalEquityGrossMinorityInterest,annualTotalEquityGrossMinorityInterest", "period1": int((datetime.now(timezone.utc).timestamp()) - 500*86400), "period2": int(datetime.now(timezone.utc).timestamp()), "merge": "false", "padTimeSeries": "true"}
        try:
            r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            if not r.ok:
                return {"Kod": symbol, "PD/DD": np.nan, "Özkaynak": np.nan, "Piyasa değeri": np.nan, "Değerleme notu": f"Kaynak HTTP {r.status_code}"}
            payload = r.json().get("timeseries", {}).get("result", [])
            values = {}
            for item in payload:
                key = item.get("meta", {}).get("type", [None])[0]
                points = item.get("quarterly", item.get("annual", []))
                if points:
                    valid_points = [x for x in points if x.get("reportedValue", {}).get("raw") is not None]
                    if valid_points:
                        values[key] = float(valid_points[-1]["reportedValue"]["raw"])
            mcap = next((v for k,v in values.items() if "MarketCap" in str(k)), np.nan)
            equity = next((v for k,v in values.items() if "Equity" in str(k) and v > 0), np.nan)
            pb = mcap / equity if pd.notna(mcap) and pd.notna(equity) and equity > 0 else np.nan
            return {"Kod": symbol, "PD/DD": pb, "Özkaynak": equity, "Piyasa değeri": mcap, "Değerleme notu": "Yaklaşık; kaynak verisi teyit edilmeli" if pd.notna(pb) else "PD/DD verisi alınamadı"}
        except Exception as exc:
            return {"Kod": symbol, "PD/DD": np.nan, "Özkaynak": np.nan, "Piyasa değeri": np.nan, "Değerleme notu": "Veri alınamadı"}

    with st.expander("PD/DD nasıl yorumlanmalı?", expanded=False):
        st.write("PD/DD = piyasa değeri / özkaynak. Düşük oran, şirketin özkaynağına göre düşük fiyatlandığını gösterebilir; fakat düşük kârlılık, zarar, yüksek risk veya özkaynak kalitesi sorunları da sebep olabilir. Bankalar ve sanayi şirketleri aynı eşiklerle kıyaslanmamalıdır.")
        st.write("Bu tarama yalnızca erişilebilen sağlayıcı verisini gösterir. Eksik oranlar sıfır kabul edilmez; canlı finansal veri erişimi garanti değildir.")

    left, right = st.columns([1, 1])
    with left:
        selected_symbol = st.selectbox("Hisse seç", list(BIST_WATCHLIST.keys()), index=0,
                                       format_func=lambda x: f"{x} — {BIST_WATCHLIST[x]}")
    with right:
        chart_interval_label = st.selectbox("Grafik periyodu", ["Günlük", "Saatlik", "Haftalık"], index=0)
    chart_params = {"Günlük": ("3mo", "1d"), "Saatlik": ("5d", "1h"), "Haftalık": ("2y", "1wk")}
    try:
        selected_data = get_yahoo_history(selected_symbol, *chart_params[chart_interval_label])
        close = selected_data["close"].astype(float)
        selected_data["EMA20"] = close.ewm(span=20, adjust=False).mean()
        selected_data["EMA50"] = close.ewm(span=50, adjust=False).mean()
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        selected_data["RSI14"] = 100 - (100 / (1 + rs))
        last = float(close.iloc[-1])
        previous = float(close.iloc[-2]) if len(close) > 1 else last
        day_change = (last / previous - 1) * 100 if previous else 0
        latest_rsi = float(selected_data["RSI14"].iloc[-1]) if pd.notna(selected_data["RSI14"].iloc[-1]) else np.nan
        ema20 = float(selected_data["EMA20"].iloc[-1])
        ema50 = float(selected_data["EMA50"].iloc[-1])
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Son fiyat", f"₺{last:,.2f}", f"{day_change:+.2f}%")
        m2.metric("RSI (14)", f"{latest_rsi:.1f}" if pd.notna(latest_rsi) else "—")
        m3.metric("EMA 20 / 50", "Pozitif" if ema20 > ema50 else "Negatif", f"EMA20 ₺{ema20:,.2f}")
        m4.metric("Son veri mumu", selected_data.index[-1].tz_convert("Europe/Istanbul").strftime("%d.%m.%Y %H:%M"))

        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=selected_data.index, open=selected_data["open"], high=selected_data["high"],
                                     low=selected_data["low"], close=selected_data["close"], name=selected_symbol))
        fig.add_trace(go.Scatter(x=selected_data.index, y=selected_data["EMA20"], name="EMA 20", line=dict(width=1.5)))
        fig.add_trace(go.Scatter(x=selected_data.index, y=selected_data["EMA50"], name="EMA 50", line=dict(width=1.5)))
        fig.update_layout(template="plotly_dark", height=520, margin=dict(l=10, r=10, t=25, b=10),
                          xaxis_rangeslider_visible=False, legend=dict(orientation="h", y=1.02),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        # Teknik görünüm: kurallı, açıklanabilir puanlama; getiri garantisi değildir.
        score = 0
        reasons = []
        if ema20 > ema50:
            score += 1; reasons.append("EMA 20, EMA 50'nin üzerinde: kısa/orta vadeli eğilim olumlu.")
        else:
            reasons.append("EMA 20, EMA 50'nin altında: eğilim zayıf veya baskı altında.")
        if pd.notna(latest_rsi) and 50 <= latest_rsi < 70:
            score += 1; reasons.append("RSI 50–70 aralığında: momentum pozitif, aşırı alım eşiğinin altında.")
        elif pd.notna(latest_rsi) and latest_rsi >= 70:
            reasons.append("RSI 70 ve üzeri: momentum güçlü olabilir, fakat aşırı alım/geri çekilme riski artar.")
        elif pd.notna(latest_rsi) and latest_rsi < 30:
            reasons.append("RSI 30 altında: aşırı satım bölgesi; tek başına dönüş sinyali değildir.")
        else:
            reasons.append("RSI 30–50 aralığında: momentum teyidi sınırlı.")
        if len(close) >= 21 and close.iloc[-1] > close.iloc[-21]:
            score += 1; reasons.append("Son 20 işlem günü kapanışı önceki seviyenin üzerinde.")
        else:
            reasons.append("Son 20 işlem gününde pozitif fiyat ivmesi teyit edilmedi.")
        if score >= 2:
            view = "Olumlu teknik görünüm"
        elif score == 1:
            view = "Karışık / izlemeye değer"
        else:
            view = "Zayıf teknik görünüm"
        st.subheader(f"{selected_symbol} · Teknik değerlendirme")
        st.markdown(f"**Özet:** {view} · {score}/3 teknik koşul olumlu")
        for reason in reasons:
            st.write(f"• {reason}")
        st.caption("Bu puan olasılık veya hedef fiyat değildir. Yalnızca grafikten hesaplanan üç basit teknik koşulu özetler.")
        st.markdown("#### Vade bazlı değerlendirme")
        st.write("**Kısa vade (birkaç gün–4 hafta):** RSI, son fiyat ivmesi ve EMA20/50 daha belirleyicidir; oynaklık ve zarar-kes seviyesi ayrıca değerlendirilmelidir.")
        st.write("**Orta vade (1–6 ay):** fiyat trendi yanında çeyreklik satış/kâr gelişimi, borçluluk, nakit akışı ve sektör koşulları gerekir.")
        st.write("**Uzun vade (6–24 ay):** rekabet avantajı, sürdürülebilir kârlılık, yatırım harcamaları, bilanço kalitesi ve değerleme birlikte incelenmelidir.")
        st.info("Uygulama bu vadeler için kesin al/sat emri veya garanti getiri üretmez. Bu sürümde kısa vadeli teknik göstergeler hesaplanır; orta/uzun vade finansal değerlendirmesi için güncel KAP verileri ayrıca bağlanmalıdır.")

        with st.expander("Şirket ne iş yapıyor, neden izlenebilir?"):
            st.write(BIST_WATCHLIST[selected_symbol] + ".")
            st.write("Şirketin ayrışmasını değerlendirirken son finansal raporlar, satış/kâr büyümesi, borçluluk, nakit akışı, sektör görünümü, değerleme ve KAP açıklamaları birlikte incelenmelidir.")
            st.write("Bu sürüm şirket faaliyet alanını genel sınıflandırma olarak verir; güncel finansal veriler ve KAP haberleri henüz otomatik bağlanmış değildir.")
    except Exception as exc:
        st.error(f"{selected_symbol} verisi şu anda alınamadı: {exc}")
        st.info("Fiyat kaynağı Yahoo Finance üzerinden deneniyor. Sembol erişimi veya sağlayıcı kısıtlaması olabilir; biraz sonra tekrar deneyebilirsin.")

    st.divider()
    st.subheader("BIST izleme sepeti · Günün öne çıkanları")
    st.caption("Bu tablo aşağıdaki izleme sepetindeki hisseleri karşılaştırır; Borsa İstanbul'un resmî tam piyasa sıralaması değildir. Günlük değişim ve hacim sağlayıcının son barına dayanır.")
    with st.spinner("İzleme sepeti verileri alınıyor…"):
        snapshot = get_bist_snapshot(tuple(universe_symbols))
    valid = snapshot.dropna(subset=["Günlük %", "Son fiyat"]).copy()
    st.markdown("#### 📚 PD/DD taraması · En düşük / en yüksek")
    with st.spinner("Erişilebilir hisselerin PD/DD verileri sorgulanıyor…"):
        valuation_rows = []
        # Sorgu sayısını makul tut: seçili evrenden ilk 45 sembol. İstenen sembol grafikte ayrıca seçilebilir.
        valuation_symbols = universe_symbols[:45]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            valuation_rows = list(pool.map(get_yahoo_valuation, valuation_symbols))
        valuation = pd.DataFrame(valuation_rows)
    if not valuation.empty and valuation["PD/DD"].notna().any():
        valued = valuation.dropna(subset=["PD/DD"]).copy()
        valued = valued[valued["PD/DD"] > 0]
        low_col, high_col = st.columns(2)
        with low_col:
            st.markdown("##### En düşük PD/DD")
            low = valued.nsmallest(10, "PD/DD").copy()
            low["Şirket"] = low["Kod"].map(BIST_WATCHLIST)
            st.dataframe(low[["Kod", "Şirket", "PD/DD", "Değerleme notu"]].style.format({"PD/DD":"{:.2f}x"}), hide_index=True, use_container_width=True)
        with high_col:
            st.markdown("##### En yüksek PD/DD")
            high = valued.nlargest(10, "PD/DD").copy()
            high["Şirket"] = high["Kod"].map(BIST_WATCHLIST)
            st.dataframe(high[["Kod", "Şirket", "PD/DD", "Değerleme notu"]].style.format({"PD/DD":"{:.2f}x"}), hide_index=True, use_container_width=True)
        st.caption("PD/DD oranları yalnızca kaynağın döndürdüğü değerlerden hesaplanır; veri eksikse hisse sıralamaya girmez. Finansal tabloların raporlama tarihi ve veri kaynağı teyit edilmelidir.")
    else:
        st.warning("Bu oturumda seçili evren için güvenilir PD/DD verisi alınamadı. Fiyat verisi mevcut olsa bile temel finansal oranlar ayrı veri kaynağı gerektirebilir; oranlar tahmin edilerek doldurulmadı.")
    if not valid.empty:
        gainers, losers, volume_col = st.columns(3)
        with gainers:
            st.markdown("#### 🟢 En çok yükselen")
            st.dataframe(valid.nlargest(5, "Günlük %")[ ["Kod", "Son fiyat", "Günlük %"] ].style.format({"Son fiyat":"₺{:,.2f}", "Günlük %":"{:+.2f}%"}), hide_index=True, use_container_width=True)
        with losers:
            st.markdown("#### 🔴 En çok düşen")
            st.dataframe(valid.nsmallest(5, "Günlük %")[ ["Kod", "Son fiyat", "Günlük %"] ].style.format({"Son fiyat":"₺{:,.2f}", "Günlük %":"{:+.2f}%"}), hide_index=True, use_container_width=True)
        with volume_col:
            st.markdown("#### 📊 İşlem değeri yüksek")
            st.dataframe(valid.nlargest(5, "Yaklaşık işlem değeri")[ ["Kod", "Son fiyat", "Yaklaşık işlem değeri"] ].style.format({"Son fiyat":"₺{:,.2f}", "Yaklaşık işlem değeri":"₺{:,.0f}"}), hide_index=True, use_container_width=True)
        st.markdown("#### Tüm izleme sepeti")
        show = valid.copy()
        show["Şirket"] = show["Kod"].map(BIST_WATCHLIST)
        show = show[["Kod", "Şirket", "Son fiyat", "Günlük %", "Hacim", "Yaklaşık işlem değeri", "Veri zamanı"]].sort_values("Günlük %", ascending=False)
        st.dataframe(show.style.format({"Son fiyat":"₺{:,.2f}", "Günlük %":"{:+.2f}%", "Hacim":"{:,.0f}", "Yaklaşık işlem değeri":"₺{:,.0f}"}, na_rep="—"), hide_index=True, use_container_width=True)
    else:
        st.warning("İzleme sepeti için geçerli veri alınamadı. Veri sağlayıcı erişimini kontrol et.")

    st.subheader("Kurum bazlı net alım / satım")
    st.info("Bu sürümde kurumların günlük net alım-satım sıralaması henüz gösterilmiyor. Bu veri, fiyat ve hacimden güvenilir biçimde çıkarılamaz; aracı kurum dağılımı veya lisanslı gerçek zamanlı veri kaynağı ayrıca entegre edilmeli. Burada uydurma kurum isimleri ya da akış rakamları gösterilmeyecek.")
    st.caption("Veri notu: Bu ekran üçüncü taraf Yahoo Finance fiyat akışını kullanır; gerçek zamanlılık veya gecikmesiz fiyat garantisi vermez. Veriler 5 dakika önbelleğe alınır. Kurumsal kullanım ve kesin seans verileri için lisanslı kaynak tercih edilmelidir.")
    st.stop()

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
  .signal-legend { background: rgba(16,26,43,.88); border: 1px solid #30425d; border-radius: 14px; padding: 14px 16px; margin-bottom: 10px; }
  .legend-row { display: flex; align-items: flex-start; gap: 10px; margin: 10px 0; }
  .legend-swatch { width: 11px; height: 11px; min-width: 11px; border-radius: 3px; margin-top: 5px; box-shadow: 0 0 12px rgba(255,255,255,.08); }
  .legend-title { color: #f1f5fb; font-weight: 750; font-size: 14px; }
  .legend-detail { color: #aebed4; font-size: 12px; line-height: 1.45; margin-top: 3px; }
  .signal-score-pill { display: inline-block; border: 1px solid #344a68; background: #15243a; color: #dce8f8; padding: 4px 9px; border-radius: 999px; font-size: 12px; }
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

    st.divider()
    st.header("🧪 Sanal işlem hesabı")
    account_size = st.number_input("Başlangıç bakiyesi ($)", min_value=100.0, max_value=10_000_000.0, value=10000.0, step=500.0, help="Sadece sanal takip hesabı; gerçek broker hesabına bağlı değildir.")
    paper_amount = st.number_input("İşlem tutarı ($)", min_value=1.0, max_value=1_000_000.0, value=100.0, step=10.0, help="Örneğin 100 $, altının fiyat hareketine göre sanal kâr/zarar hesaplar. Kaldıraç ve broker lotu modellenmez.")
    st.caption("Aşağıdaki AL / SAT düğmeleri yalnızca sanal işlem kaydı oluşturur; gerçek emir göndermez.")
    enable_mtf = st.checkbox("Ek API çağrılarıyla çoklu zaman dilimi kontrolü", value=False, help="Açılırsa 1h, 4h ve günlük veri için ek API çağrıları yapılabilir; API kotanı tüketebilir.")
    enable_alerts = st.checkbox("Telegram bildirimi özelliğini göster", value=False)
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

    # Some feeds may label candles with suspicious future timestamps.
    # Remove only clearly future bars when at least 55 valid historical bars remain.
    now_utc = pd.Timestamp.now(tz="UTC")
    future_mask = data.index > (now_utc + pd.Timedelta(minutes=5))
    if future_mask.any():
        historical = data.loc[~future_mask]
        if len(historical) >= 55:
            data = historical

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
# EK ANALİZ FONKSİYONLARI
# --------------------------------------------------
def classify_regime(frame, atr_value, ema_fast_value, ema_slow_value, close_value):
    if pd.isna(atr_value) or close_value <= 0:
        return "Veri yetersiz", "Piyasa rejimi için ATR verisi bulunamadı."
    atr_pct = float(atr_value) / float(close_value) * 100
    ema_gap_pct = abs(float(ema_fast_value) - float(ema_slow_value)) / float(close_value) * 100
    if atr_pct >= 0.8:
        return "Yüksek volatilite", f"ATR yaklaşık %{atr_pct:.2f}; hareket aralığı yükselmiş."
    if ema_gap_pct >= 0.25:
        direction = "yukarı" if ema_fast_value > ema_slow_value else "aşağı"
        return "Trend piyasası", f"EMA'lar ayrışmış; kısa vadeli yön {direction}."
    return "Yatay / zayıf trend", f"EMA farkı %{ema_gap_pct:.2f}; trend gücü sınırlı olabilir."


def load_paper_trades(path="paper_trades.json"):
    """Load simulated trades from the app working directory, if available."""
    import json
    from pathlib import Path
    file_path = Path(path)
    if not file_path.exists():
        return []
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_paper_trades(trades, path="paper_trades.json"):
    """Save simulated trades locally; cloud restarts may reset local files."""
    import json
    from pathlib import Path
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(trades, f, ensure_ascii=False, indent=2, default=str)


def resample_ohlc(frame, rule):
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if "volume" in frame.columns:
        agg["volume"] = "sum"
    return frame.resample(rule).agg(agg).dropna(subset=["open", "high", "low", "close"])


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
        f"Türkiye saati: {last_time.tz_convert('Europe/Istanbul').strftime('%Y-%m-%d %H:%M:%S %Z')} | "
        f"Şu an UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
        f"Fark: {age_hours:.2f} saat"
    )

    if age_hours < -0.1:
        st.warning(
            "API son mum zamanını gelecekte gösteriyor. Gelecek tarihli mumlar yeterli geçmiş veri bulunduğunda analizden çıkarılır; "
            "kaynak zaman damgası yine de doğrulanmalıdır. Bu durumda sinyali temkinli değerlendir."
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

# --------------------------------------------------
# SANAL İŞLEM KAYDI (GERÇEK EMİR GÖNDERMEZ)
# --------------------------------------------------
import uuid

if "paper_trades" not in st.session_state:
    st.session_state.paper_trades = load_paper_trades()

# Actions are rendered in the sidebar, after a current market price is available.
with st.sidebar:
    st.divider()
    st.subheader("🧾 Sanal işlem aç / kapat")
    st.caption(f"Referans fiyat: ${price:,.2f} · Güncel seçili grafiğin son kapanışı")
    if st.button("🟢 AL — sanal pozisyon aç", use_container_width=True, key="paper_buy"):
        if paper_amount > 0 and price > 0:
            st.session_state.paper_trades.append({
                "id": str(uuid.uuid4())[:8], "side": "AL", "notional": float(paper_amount),
                "entry_price": float(price), "quantity": float(paper_amount) / float(price),
                "opened_at": datetime.now(timezone.utc).isoformat(), "status": "Açık",
                "exit_price": None, "closed_at": None, "pnl": None, "pnl_pct": None
            })
            save_paper_trades(st.session_state.paper_trades)
            st.success(f"${paper_amount:,.2f} tutarında sanal AL pozisyonu açıldı.")
    if st.button("🔴 SAT — sanal kısa pozisyon aç", use_container_width=True, key="paper_sell"):
        if paper_amount > 0 and price > 0:
            st.session_state.paper_trades.append({
                "id": str(uuid.uuid4())[:8], "side": "SAT", "notional": float(paper_amount),
                "entry_price": float(price), "quantity": float(paper_amount) / float(price),
                "opened_at": datetime.now(timezone.utc).isoformat(), "status": "Açık",
                "exit_price": None, "closed_at": None, "pnl": None, "pnl_pct": None
            })
            save_paper_trades(st.session_state.paper_trades)
            st.success(f"${paper_amount:,.2f} tutarında sanal SAT pozisyonu açıldı.")

    open_trades_sidebar = [t for t in st.session_state.paper_trades if t.get("status") == "Açık"]
    if open_trades_sidebar:
        close_options = {f"{t['id']} · {t['side']} · ${t['notional']:,.2f} · giriş ${t['entry_price']:,.2f}": t["id"] for t in open_trades_sidebar}
        selected_close_label = st.selectbox("Kapatılacak açık pozisyon", list(close_options.keys()), key="paper_close_select")
        if st.button("Pozisyonu mevcut fiyattan kapat", use_container_width=True, key="paper_close"):
            selected_id = close_options[selected_close_label]
            for trade in st.session_state.paper_trades:
                if trade.get("id") == selected_id and trade.get("status") == "Açık":
                    direction = 1 if trade["side"] == "AL" else -1
                    pnl = (float(price) - float(trade["entry_price"])) * float(trade["quantity"]) * direction
                    trade["exit_price"] = float(price)
                    trade["closed_at"] = datetime.now(timezone.utc).isoformat()
                    trade["pnl"] = round(pnl, 4)
                    trade["pnl_pct"] = round(pnl / float(trade["notional"]) * 100, 4)
                    trade["status"] = "Kapalı"
                    break
            save_paper_trades(st.session_state.paper_trades)
            st.success("Sanal pozisyon kapatıldı ve sonucu kaydedildi.")
            st.rerun()
    else:
        st.caption("Henüz açık sanal pozisyon yok.")

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
# DESTEK/DİRENÇ, REJİM VE POZİSYON BOYUTU
# --------------------------------------------------
regime_name, regime_detail = classify_regime(data, atr, ema_f, ema_s, price)
lookback = min(50, len(data))
recent = data.tail(lookback)
resistance = float(recent["high"].max())
support = float(recent["low"].min())

# Eski risk-yuzdesi pozisyon boyutlandırması kaldırıldı; sanal işlem tutarı paper_amount ile yönetilir.

# --------------------------------------------------
# DASHBOARD ÖZETİ
# --------------------------------------------------
st.markdown("### Piyasa özeti")
local_tz = "Europe/Istanbul"
last_time_local = last_time.tz_convert(local_tz) if getattr(last_time, "tzinfo", None) is not None else last_time.tz_localize("UTC").tz_convert(local_tz)
st.caption(f"Kaynak: {mode}  ·  Mum aralığı: {interval}  ·  Son mum: {last_time_local.strftime('%Y-%m-%d %H:%M %Z')} (Türkiye saati)")

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
    "Yön puanı",
    f"{score:+d} / 3",
    "3 teknik kriterin toplamı"
)

c4.metric(
    "Teknik görünüm",
    signal
)

st.subheader("Sinyal analizi")
st.caption("Yön puanı, üç basit kontrolün toplamıdır: EMA trendi (+1/−1), fiyatın hızlı EMA üstünde/altında olması (+1/−1) ve RSI momentumu (+1/−1). Pozitif puan yukarı, negatif puan aşağı eğilimi anlatır; başarı olasılığı veya garanti değildir.")

if signal == "AL eğilimi":
    card_class, signal_color = "buy", "#56e0ad"
elif signal == "SAT eğilimi":
    card_class, signal_color = "sell", "#ff8193"
else:
    card_class, signal_color = "neutral", "#f3d27c"

# Pie/donut breakdown counts the three rules, not a claimed probability of success.
criterion_directions = [
    "AL" if trend_up else ("SAT" if trend_down else "NÖTR"),
    "AL" if price_above_fast else ("SAT" if price_below_fast else "NÖTR"),
    "AL" if (rsi_rising and 40 <= rsi <= 70) else ("SAT" if (rsi_falling and 30 <= rsi <= 60) else "NÖTR"),
]
buy_count = criterion_directions.count("AL")
sell_count = criterion_directions.count("SAT")
neutral_count = criterion_directions.count("NÖTR")
labels = [label for label, count in [("AL", buy_count), ("SAT", sell_count), ("NÖTR", neutral_count)] if count > 0]
values = [count for count in [buy_count, sell_count, neutral_count] if count > 0]
colors = {"AL": "#35d39a", "SAT": "#ff647c", "NÖTR": "#f3c969"}
chart_colors = [colors[label] for label in labels]

donut = go.Figure(data=[go.Pie(
    labels=labels,
    values=values,
    hole=0.68,
    sort=False,
    direction="clockwise",
    marker=dict(colors=chart_colors, line=dict(color="#101a2b", width=4)),
    texttemplate="%{label}<br>%{percent}",
    textposition="inside",
    insidetextorientation="horizontal",
    textfont=dict(size=13, color="#07111e"),
    hovertemplate="%{label}: %{value}/3 kriter (%{percent})<extra></extra>",
    showlegend=False
)])
donut.update_layout(
    height=310,
    margin=dict(l=4, r=4, t=10, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#d9e4f3"),
    annotations=[dict(text=f"{score:+d}<br><span style='font-size:10px'>YÖN PUANI</span>", x=0.5, y=0.5, showarrow=False, font=dict(size=24, color="#f5f8ff"))]
)

signal_cols = st.columns([1.0, 1.1, 1.25], gap="medium")
with signal_cols[0]:
    st.markdown(
        f'<div class="signal-card {card_class}">'
        f'<div class="signal-eyebrow">Mevcut teknik görünüm</div>'
        f'<div class="signal-head" style="color:{signal_color}">{signal}</div>'
        f'<div class="signal-body">Yön puanı: <b>{score:+d} / 3</b><br>Son kapanış: <b>${price:,.2f}</b><br>RSI: <b>{rsi:.1f} / 100</b></div>'
        f'<div style="margin-top:12px"><span class="signal-score-pill">3 kural · şeffaf skor</span></div>'
        f'</div>',
        unsafe_allow_html=True
    )
with signal_cols[1]:
    st.markdown("**Teknik yön dağılımı**")
    st.plotly_chart(donut, use_container_width=True, config={"displayModeBar": False})
with signal_cols[2]:
    st.markdown("**Sinyalin arkasındaki nedenler**")
    legend_items = [
        ("AL", buy_count, "#35d39a", " · ".join(buy_reasons) if buy_reasons else "AL yönünü destekleyen kriter yok."),
        ("SAT", sell_count, "#ff647c", " · ".join(sell_reasons) if sell_reasons else "SAT yönünü destekleyen kriter yok."),
        ("NÖTR", neutral_count, "#f3c969", " · ".join(neutral_reasons) if neutral_reasons else "Nötr kriter yok."),
    ]
    for label, count, color, detail in legend_items:
        pct = count / 3 * 100
        st.markdown(
            f'<div class="signal-legend"><div class="legend-row"><span class="legend-swatch" style="background:{color}"></span>'
            f'<div><div class="legend-title">{label} · {pct:.0f}% <span style="color:#9fb0c9;font-weight:500">({count}/3 kriter)</span></div>'
            f'<div class="legend-detail">{detail}</div></div></div></div>',
            unsafe_allow_html=True
        )
    st.markdown('<div class="small-note">Yüzdeler yalnızca 3 teknik kuralın dağılımıdır; kâr etme olasılığı veya başarı oranı değildir.</div>', unsafe_allow_html=True)

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
    f"Son mum: {last_time_local.strftime('%Y-%m-%d %H:%M %Z')} (Türkiye saati)"
)

# --------------------------------------------------
# İLERİ ANALİZ MODÜLLERİ
# --------------------------------------------------
st.subheader("Piyasa yapısı ve işlem planı")
mc1, mc2, mc3, mc4 = st.columns(4, gap="medium")
mc1.metric("Piyasa rejimi", regime_name)
mc2.metric("Yakın destek", f"${support:,.2f}")
mc3.metric("Yakın direnç", f"${resistance:,.2f}")
mc4.metric("ATR / fiyat", f"{(float(atr) / price * 100):.2f}%" if pd.notna(atr) and price else "—")
st.caption(regime_detail + " Destek/direnç, geçmiş mumlardaki dönüş noktalarından türetilen yaklaşık fiyat bölgeleridir; kesin veya değişmez seviyeler değildir.")


if enable_mtf:
    st.subheader("Çoklu zaman dilimi kontrolü")
    st.warning("Bu kontrol seçili veri setinden daha yüksek zaman dilimleri üretir; API'den bağımsız yeni veri çekmez. Bu nedenle sonuçlar yalnızca mevcut veri çözünürlüğünün izin verdiği ölçüde anlamlıdır.")
    try:
        if interval == "1h":
            tf_frames = {"1 saat": data, "4 saat (resample)": resample_ohlc(data, "4h"), "Günlük (resample)": resample_ohlc(data, "1D")}
        elif interval == "4h":
            tf_frames = {"4 saat": data, "Günlük (resample)": resample_ohlc(data, "1D")}
        else:
            tf_frames = {"Günlük": data}
        tf_results = []
        for tf_name, tf_frame in tf_frames.items():
            if len(tf_frame) < max(ema_slow, 10):
                tf_results.append({"Zaman dilimi": tf_name, "Yön": "Yetersiz veri", "Kapanış": float(tf_frame["close"].iloc[-1]) if len(tf_frame) else np.nan})
                continue
            tf_fast = tf_frame["close"].ewm(span=ema_fast, adjust=False).mean().iloc[-1]
            tf_slow = tf_frame["close"].ewm(span=ema_slow, adjust=False).mean().iloc[-1]
            tf_direction = "AL" if tf_fast > tf_slow else "SAT" if tf_fast < tf_slow else "NÖTR"
            tf_results.append({"Zaman dilimi": tf_name, "Yön": tf_direction, "Kapanış": float(tf_frame["close"].iloc[-1])})
        st.dataframe(pd.DataFrame(tf_results), use_container_width=True, hide_index=True)
        directions = [r["Yön"] for r in tf_results if r["Yön"] in ("AL", "SAT")]
        if directions and len(set(directions)) == 1:
            st.success(f"Mevcut veri içinde hesaplanan zaman dilimleri {directions[0]} yönünde uyumlu.")
        elif directions:
            st.warning("Zaman dilimleri arasında yön ayrışması var.")
        else:
            st.info("Yeterli zaman dilimi verisi yok.")
    except Exception as exc:
        st.warning(f"Çoklu zaman dilimi analizi oluşturulamadı: {exc}")


# --------------------------------------------------
# KULLANICININ SANAL İŞLEM PERFORMANSI (BACKTEST DEĞİL)
# --------------------------------------------------
st.subheader("Senin sanal işlemlerin · Kâr / zarar takibi")
st.caption("Bu bölüm yalnızca senin AL/SAT düğmeleriyle açıp kapattığın sanal işlemleri hesaplar. Geçmiş mumlara otomatik strateji uygulamaz ve gerçek emir göndermez. Açık işlemlerin kâr/zararı son kapanış fiyatına göre anlık tahmindir.")

paper_trades = st.session_state.paper_trades
closed_trades = [t for t in paper_trades if t.get("status") == "Kapalı"]
open_trades = [t for t in paper_trades if t.get("status") == "Açık"]
realized_pnl = sum(float(t.get("pnl") or 0) for t in closed_trades)
open_pnl = sum((price - float(t["entry_price"])) * float(t["quantity"]) * (1 if t["side"] == "AL" else -1) for t in open_trades)
wins = sum(1 for t in closed_trades if float(t.get("pnl") or 0) > 0)
losses = sum(1 for t in closed_trades if float(t.get("pnl") or 0) < 0)
win_rate = wins / len(closed_trades) * 100 if closed_trades else 0.0

pc1, pc2, pc3, pc4, pc5, pc6 = st.columns(6, gap="small")
pc1.metric("Başlangıç bakiyesi", f"${account_size:,.2f}")
pc2.metric("Kapanan işlem", f"{len(closed_trades)}")
pc3.metric("Kazanma oranı", f"{win_rate:.1f}%", help="Kârlı kapanan işlemler / tüm kapanan işlemler. İşlem yoksa %0 gösterilir.")
pc4.metric("Gerçekleşmiş sanal K/Z", f"${realized_pnl:+,.2f}")
pc5.metric("Açık işlemlerin K/Z'si", f"${open_pnl:+,.2f}")
pc6.metric("Tahmini sanal bakiye", f"${account_size + realized_pnl + open_pnl:,.2f}")

if open_trades:
    open_rows = []
    for t in open_trades:
        direction = 1 if t["side"] == "AL" else -1
        live_pnl = (price - float(t["entry_price"])) * float(t["quantity"]) * direction
        open_rows.append({"ID": t["id"], "Yön": t["side"], "Tutar ($)": round(float(t["notional"]), 2), "Giriş fiyatı": round(float(t["entry_price"]), 2), "Son fiyat": round(price, 2), "Açık K/Z ($)": round(live_pnl, 2), "Getiri (%)": round(live_pnl / float(t["notional"]) * 100, 2), "Açılış (UTC)": t["opened_at"]})
    st.markdown("**Açık pozisyonlar**")
    st.dataframe(pd.DataFrame(open_rows), use_container_width=True, hide_index=True)

if paper_trades:
    history_rows = []
    for t in reversed(paper_trades):
        direction = 1 if t["side"] == "AL" else -1
        live_pnl = (price - float(t["entry_price"])) * float(t["quantity"]) * direction if t.get("status") == "Açık" else float(t.get("pnl") or 0)
        history_rows.append({"ID": t["id"], "Yön": t["side"], "Tutar ($)": round(float(t["notional"]), 2), "Giriş": round(float(t["entry_price"]), 2), "Çıkış": round(float(t["exit_price"]), 2) if t.get("exit_price") is not None else "—", "Durum": t["status"], "Sanal K/Z ($)": round(live_pnl, 2), "Getiri (%)": round(live_pnl / float(t["notional"]) * 100, 2), "Açılış (UTC)": t["opened_at"], "Kapanış (UTC)": t.get("closed_at") or "—"})
    history_df = pd.DataFrame(history_rows)
    st.markdown("**İşlem geçmişin**")
    st.dataframe(history_df, use_container_width=True, hide_index=True)
    st.download_button("İşlem geçmişini CSV olarak indir", history_df.to_csv(index=False).encode("utf-8-sig"), file_name="sanal_islem_gecmisi.csv", mime="text/csv")
    if st.button("Tüm sanal işlem geçmişini sil", key="paper_clear_history"):
        st.session_state.paper_trades = []
        save_paper_trades([])
        st.rerun()
else:
    st.info("Henüz sanal işlem yok. Soldaki panelden örneğin 100 $ tutarında AL veya SAT işlemi açıp, sonra fiyatı izleyebilir ve istediğin zaman kapatabilirsin.")

st.warning("Kayıtlar bu uygulama örneğinin yerel dosyasına yazılır. Streamlit Cloud yeniden başlatıldığında veya uygulama yeniden dağıtıldığında yerel dosya sıfırlanabilir; kalıcı yedek için CSV indir. Hesaplamalar kaldıraç, swap, spread ve komisyon içermez.")

if enable_alerts:
    st.subheader("Telegram bildirim kurulumu")
    st.info("Güvenli bildirim için Streamlit Secrets içine TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID eklenebilir. Bu sürüm otomatik mesaj göndermiyor; tekrar eden mesajları ve yanlış alarmları önlemek için bildirim gönderimi ayrıca opt-in düğmesiyle kurulmalıdır.")
    token_present = bool(st.secrets.get("TELEGRAM_BOT_TOKEN", ""))
    chat_present = bool(st.secrets.get("TELEGRAM_CHAT_ID", ""))
    st.write(f"Bot token: {'tanımlı' if token_present else 'tanımlı değil'} · Chat ID: {'tanımlı' if chat_present else 'tanımlı değil'}")

# --------------------------------------------------
# GRAFİK
# --------------------------------------------------
st.subheader("Fiyat grafiği: destek ve direnç seviyeleri")
st.markdown('<span style="color:#45d6a5;font-weight:800">YEŞİL KESİKLİ ÇİZGİ = DESTEK</span> · <span style="color:#ff7185;font-weight:800">KIRMIZI KESİKLİ ÇİZGİ = DİRENÇ</span> · <span style="color:#42d6a4;font-weight:800">Turkuaz = hızlı EMA</span> · <span style="color:#ffbf69;font-weight:800">Turuncu = yavaş EMA</span>', unsafe_allow_html=True)
st.caption("Destek, fiyatın düşüşte tutunabileceği; direnç ise yükselişte zorlanabileceği yaklaşık bölgedir. Seviyeler seçili veri setindeki son 50 mumun yerel dip/tepelerinden hesaplanır; garanti değildir.")

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

# Grafikte net görülebilen yatay destek/direnç çizgileri (son 50 mum).
level_window = data.tail(min(50, len(data)))
# Yerel dipler/tepelerden seviye adayları; en yakın seviyeler seçilir.
low_vals = level_window["low"].to_numpy(dtype=float)
high_vals = level_window["high"].to_numpy(dtype=float)
close_vals = level_window["close"].to_numpy(dtype=float)
low_pivots = [float(low_vals[i]) for i in range(2, len(low_vals)-2) if low_vals[i] <= min(low_vals[i-2:i+3])]
high_pivots = [float(high_vals[i]) for i in range(2, len(high_vals)-2) if high_vals[i] >= max(high_vals[i-2:i+3])]
# Fiyatın altındaki en yakın iki farklı destek, üstündeki en yakın iki farklı direnç.
def distinct_levels(values, current, below=True, tolerance=0.0015):
    candidates = sorted([v for v in values if (v < current if below else v > current)], reverse=below)
    chosen = []
    for v in candidates:
        if all(abs(v-u) / max(abs(u), 1e-9) > tolerance for u in chosen):
            chosen.append(v)
        if len(chosen) == 2:
            break
    return chosen

support_levels = distinct_levels(low_pivots + [support], price, below=True)
resistance_levels = distinct_levels(high_pivots + [resistance], price, below=False)
# Eğer fiyat yeni zirve/dipteyse en yakın görünür sınırı yine göster.
if not support_levels and support < price:
    support_levels = [support]
if not resistance_levels and resistance > price:
    resistance_levels = [resistance]
for i, level in enumerate(support_levels):
    fig.add_hline(y=level, line_dash="dash", line_color="#45d6a5", line_width=2, annotation_text=f"DESTEK {i+1}  ${level:,.2f}", annotation_position="bottom right", annotation_font_color="#45d6a5")
for i, level in enumerate(resistance_levels):
    fig.add_hline(y=level, line_dash="dash", line_color="#ff7185", line_width=2, annotation_text=f"DİRENÇ {i+1}  ${level:,.2f}", annotation_position="top right", annotation_font_color="#ff7185")

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
    st.subheader("RSI · Momentum ve bölgeler")
    st.caption("RSI fiyat grafiğindeki destek/direnç değildir; momentum göstergesidir. 30 altı zayıf/aşırı satım, 50 orta çizgi, 70 üstü güçlü/aşırı alım bölgesi olarak izlenir. Bu yatay eşikler fiyat seviyesi değil RSI puanıdır.")

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

    rsi_fig.add_hline(y=70, line_dash="dash", line_color="#ff7185", annotation_text="70 · yüksek/aşırı alım", annotation_position="top left")
    rsi_fig.add_hline(y=50, line_dash="dot", line_color="#9aa9bd", annotation_text="50 · orta çizgi", annotation_position="bottom left")
    rsi_fig.add_hline(y=30, line_dash="dash", line_color="#45d6a5", annotation_text="30 · düşük/aşırı satım", annotation_position="bottom left")

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
    "Bilgilendirme: AL/SAT düğmeleri yalnızca sanal kayıt oluşturur. K/Z tahminidir; komisyon, spread, kayma, kaldıraç ve broker sözleşme koşulları modellenmez. Tek başına alım-satım kararı için kullanılmamalıdır."
)
