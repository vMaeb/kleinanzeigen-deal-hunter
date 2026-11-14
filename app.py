
import os, sqlite3, math, json
from datetime import datetime
from urllib.parse import urlparse
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
APP_TITLE = "Kleinanzeigen Deal Hunter"
DB_PATH = os.getenv("DB_PATH", "data/deals.db")
CENTER = (51.338, 7.043)  # Velbert, approximate city center

CATEGORIES = [
    "Elektronik", "Bilgisayar ve parçaları", "Telefon", "Ev aletleri",
    "Mobilya", "Saat ve mücevher", "Otomobil ve motosiklet", "Diğer"
]

def db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            market_price REAL NOT NULL,
            city TEXT,
            latitude REAL,
            longitude REAL,
            condition_text TEXT,
            url TEXT,
            source TEXT DEFAULT 'manual',
            listing_date TEXT,
            created_at TEXT NOT NULL
        )
    """)
    con.commit()
    return con

def distance_km(lat, lon):
    if lat is None or lon is None:
        return None
    lat1, lon1 = map(math.radians, CENTER)
    lat2, lon2 = math.radians(float(lat)), math.radians(float(lon))
    dlat, dlon = lat2-lat1, lon2-lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371 * 2 * math.asin(math.sqrt(a))

def normalize_url(value):
    value = str(value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    return value

def add_listing(row, source="import"):
    con = db()
    con.execute("""
      INSERT INTO listings
      (title,category,price,market_price,city,latitude,longitude,condition_text,url,source,listing_date,created_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        str(row.get("title","")).strip(),
        str(row.get("category","Diğer")),
        float(row.get("price",0)),
        float(row.get("market_price",0)),
        str(row.get("city","")),
        float(row["latitude"]) if pd.notna(row.get("latitude")) and str(row.get("latitude",""))!="" else None,
        float(row["longitude"]) if pd.notna(row.get("longitude")) and str(row.get("longitude",""))!="" else None,
        str(row.get("condition","")),
        normalize_url(row.get("url","")),
        source,
        str(row.get("listing_date","")),
        datetime.now().isoformat(timespec="seconds")
    ))
    con.commit()
    con.close()

def get_listings():
    con = db()
    df = pd.read_sql_query("SELECT * FROM listings ORDER BY created_at DESC", con)
    con.close()
    if df.empty:
        return df
    df["discount_pct"] = ((df["market_price"] - df["price"]) / df["market_price"] * 100).round(1)
    df["savings_eur"] = (df["market_price"] - df["price"]).round(2)
    df["distance_km"] = df.apply(lambda r: distance_km(r.latitude, r.longitude), axis=1)
    df["deal_score"] = df.apply(lambda r: max(0, min(100, round(r.discount_pct * 1.5))), axis=1)
    return df

def provider_scan():
    """Calls an explicitly authorized listing provider; does not scrape Kleinanzeigen."""
    endpoint = os.getenv("AUTHORIZED_LISTINGS_API_URL", "").strip()
    token = os.getenv("AUTHORIZED_LISTINGS_API_TOKEN", "").strip()
    if not endpoint or not token:
        return 0, "Canlı tarama henüz bağlanmadı. İzinli veri sağlayıcısının API adresi ve anahtarı .env dosyasına eklenmeli."
    try:
        response = requests.get(
            endpoint,
            headers={"Authorization": f"Bearer {token}", "Accept":"application/json"},
            params={"center":"Velbert, Germany", "radius_km":50, "minimum_discount_pct":40, "categories":"all"},
            timeout=25
        )
        response.raise_for_status()
        payload = response.json()
        items = payload.get("listings", payload if isinstance(payload, list) else [])
        count = 0
        for item in items:
            required = ["title", "price", "market_price"]
            if not all(k in item for k in required):
                continue
            if float(item["market_price"]) <= 0:
                continue
            if (float(item["market_price"])-float(item["price"]))/float(item["market_price"])*100 < 40:
                continue
            add_listing(item, source="authorized_api")
            count += 1
        return count, f"İzinli sağlayıcıdan {count} uygun ilan alındı."
    except Exception as exc:
        return 0, f"Sağlayıcı bağlantısı başarısız: {exc}"

st.set_page_config(page_title=APP_TITLE, page_icon="🔎", layout="wide")
st.title("🔎 Kleinanzeigen Deal Hunter")
st.caption("Velbert merkezli 50 km • Tüm kategoriler • Minimum %40 indirim")
st.info("Bu sürüm çalışan bir web uygulaması iskeletidir. Gerçek Kleinanzeigen ilanlarını otomatik çekmek için kullanım koşullarına uygun, yetkili bir veri sağlayıcısı bağlantısı gerekir. Yetkisiz scraping yapılmaz.")

with st.sidebar:
    st.header("Arama ayarları")
    st.text_input("Merkez", value="Velbert, Germany", disabled=True)
    radius = st.slider("Yarıçap (km)", 5, 150, 50, 5)
    min_discount = st.slider("Minimum indirim (%)", 10, 80, 40, 5)
    category_filter = st.selectbox("Kategori", ["Tümü"] + CATEGORIES)
    sort_by = st.selectbox("Sıralama", ["En yüksek indirim", "En düşük fiyat", "En yüksek tasarruf"])
    st.divider()
    if st.button("↻ İzinli kaynaktan tara", use_container_width=True):
        with st.spinner("Veri sağlayıcısı kontrol ediliyor..."):
            n, msg = provider_scan()
        st.success(msg) if n else st.warning(msg)

tab1, tab2, tab3 = st.tabs(["🎯 Fırsatlar", "＋ İlan ekle", "⚙️ Otomatik tarama"])

with tab1:
    df = get_listings()
    if not df.empty:
        if category_filter != "Tümü":
            df = df[df.category == category_filter]
        df = df[df.discount_pct >= min_discount]
        df = df[(df.distance_km.isna()) | (df.distance_km <= radius)]
        if sort_by == "En yüksek indirim":
            df = df.sort_values("discount_pct", ascending=False)
        elif sort_by == "En düşük fiyat":
            df = df.sort_values("price", ascending=True)
        else:
            df = df.sort_values("savings_eur", ascending=False)
    c1,c2,c3 = st.columns(3)
    c1.metric("Uygun fırsat", len(df))
    c2.metric("En yüksek indirim", f"%{df.discount_pct.max():.1f}" if not df.empty else "—")
    c3.metric("Toplam potansiyel fiyat farkı", f"{df.savings_eur.sum():,.0f} €" if not df.empty else "—")
    if df.empty:
        st.warning("Henüz eşleşen ilan yok. İlan ekleyebilir veya izinli veri sağlayıcısı bağlayabilirsin.")
    else:
        for _, r in df.iterrows():
            with st.container(border=True):
                left, mid, right = st.columns([5,2,2])
                left.subheader(r["title"])
                left.caption(f'{r["category"]} · {r["city"] or "Konum belirtilmemiş"} · {r["condition_text"] or "Kondisyon belirtilmemiş"}')
                left.write(f'Piyasa tahmini: **{r["market_price"]:,.2f} €**  ·  Tasarruf farkı: **{r["savings_eur"]:,.2f} €**')
                mid.metric("İlan fiyatı", f'{r["price"]:,.2f} €')
                right.metric("İndirim", f'%{r["discount_pct"]:.1f}')
                if pd.notna(r["distance_km"]):
                    st.caption(f'Velbert merkezine yaklaşık {r["distance_km"]:.1f} km')
                if r["url"]:
                    st.link_button("Orijinal ilana git", r["url"])
                st.caption(f'Kaynak: {r["source"]} · Fırsat puanı: {r["deal_score"]}/100')
    st.download_button("Sonuçları CSV indir", (df.to_csv(index=False) if not df.empty else "title,price,market_price\n").encode("utf-8-sig"),
                       file_name="deal_hunter_firsatlar.csv", mime="text/csv")

with tab2:
    st.subheader("İlanı manuel ekle")
    with st.form("add_listing_form"):
        title = st.text_input("Ürün başlığı", placeholder="Örn. Apple MacBook Pro M2")
        c1,c2 = st.columns(2)
        category = c1.selectbox("Kategori", CATEGORIES)
        condition = c2.selectbox("Kondisyon", ["Yeni", "Çok iyi", "İyi", "Kullanılmış", "Belirtilmemiş"])
        c1,c2 = st.columns(2)
        price = c1.number_input("İlan fiyatı (€)", min_value=0.0, step=10.0)
        market_price = c2.number_input("Tahmini piyasa fiyatı (€)", min_value=0.0, step=10.0)
        city = st.text_input("Şehir", value="Velbert")
        c1,c2 = st.columns(2)
        lat = c1.number_input("Enlem (isteğe bağlı)", value=0.0, format="%.6f")
        lon = c2.number_input("Boylam (isteğe bağlı)", value=0.0, format="%.6f")
        url = st.text_input("İlan bağlantısı")
        submitted = st.form_submit_button("İlanı kaydet")
        if submitted:
            if not title.strip() or price <= 0 or market_price <= 0:
                st.error("Başlık, ilan fiyatı ve piyasa fiyatı zorunludur.")
            else:
                add_listing({"title":title,"category":category,"price":price,"market_price":market_price,
                             "city":city,"latitude":lat if lat else None,"longitude":lon if lon else None,
                             "condition":condition,"url":url}, source="manual")
                st.success("İlan kaydedildi.")

    st.subheader("CSV ile toplu içe aktar")
    st.caption("Gerekli sütunlar: title, category, price, market_price. İsteğe bağlı: city, latitude, longitude, condition, url, listing_date.")
    upload = st.file_uploader("CSV dosyası seç", type=["csv"])
    if upload is not None and st.button("CSV ilanlarını içe aktar"):
        try:
            imported = pd.read_csv(upload)
            needed = {"title","category","price","market_price"}
            if not needed.issubset(imported.columns):
                st.error("CSV gerekli sütunları içermiyor.")
            else:
                for _, row in imported.iterrows():
                    add_listing(row, source="csv_import")
                st.success(f"{len(imported)} ilan içe aktarıldı.")
        except Exception as e:
            st.error(f"CSV okunamadı: {e}")

with tab3:
    st.subheader("Otomatik tarama bağlantısı")
    st.write("Arka plan taraması için kullanım koşullarına uygun bir API/veri sağlayıcısı gerekir. Sağlayıcı, aşağıdaki JSON biçiminde ilan döndürmelidir:")
    st.code(json.dumps({"listings":[{"title":"Ürün adı","category":"Elektronik","price":250,"market_price":450,
        "city":"Essen","latitude":51.4556,"longitude":7.0116,"condition":"İyi",
        "url":"https://www.kleinanzeigen.de/s-anzeige/...","listing_date":"2026-11-14"}]}, ensure_ascii=False, indent=2), language="json")
    st.write("Gerekli ortam değişkenleri:")
    st.code("AUTHORIZED_LISTINGS_API_URL=https://your-authorized-provider.example/api/listings\nAUTHORIZED_LISTINGS_API_TOKEN=your_token")
    st.warning("Piyasa fiyatı, aynı model/varyant ve benzer kondisyonlu emsallerden doğrulanmalıdır. Sağlayıcının market_price alanı bu tahmini sağlamalıdır.")
    st.subheader("Veri ve gizlilik")
    st.write("İlan kayıtları yerel SQLite veritabanında tutulur. Bu örnek uygulama herhangi bir Kleinanzeigen hesabına giriş yapmaz ve ilanlara otomatik mesaj göndermez.")
