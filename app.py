
import streamlit as st

st.set_page_config(
    page_title="KDH - Deal Hunter",
    page_icon="🔎",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(140deg, #071a36, #102e59);
    color: white;
}
h1, h2, h3, p, label {
    color: white !important;
}
div[data-testid="stMetric"] {
    background: #153b70;
    padding: 15px;
    border-radius: 12px;
}
.stButton button {
    background: #1685ff;
    color: white;
    border-radius: 10px;
    border: 0;
}
</style>
""", unsafe_allow_html=True)

if "offers" not in st.session_state:
    st.session_state.offers = []

lang = st.sidebar.selectbox(
    "Sprache / Dil",
    ["Türkçe", "Deutsch"]
)

tr = lang == "Türkçe"

title = "KDH – Fırsat Avcısı" if tr else "KDH – Deal Hunter"
st.title("🔎 " + title)

st.caption(
    "Velbert • 50 km • Minimum %40 indirim"
    if tr else
    "Velbert • 50 km • Mindestens 40% Rabatt"
)

st.sidebar.header("⚙️ " + ("Ayarlar" if tr else "Einstellungen"))

city = st.sidebar.text_input(
    "Merkez / Zentrum",
    "Velbert"
)

radius = st.sidebar.selectbox(
    "Mesafe / Entfernung",
    [10, 20, 30, 50, 75, 100],
    index=3
)

minimum = st.sidebar.slider(
    "Minimum indirim / Mindestrabatt",
    10, 90, 40
)

categories = [
    "Elektronik", "Bilgisayar", "Telefon",
    "Beyaz eşya", "Mobilya", "Saat ve takı",
    "Araba", "Motosiklet", "Diğer"
]

categories_de = [
    "Elektronik", "Computer", "Handys",
    "Haushaltsgeräte", "Möbel", "Uhren und Schmuck",
    "Autos", "Motorräder", "Sonstiges"
]

st.subheader(
    "➕ Yeni ilan ekle" if tr else "➕ Neues Angebot hinzufügen"
)

with st.form("offer_form"):
    name = st.text_input(
        "Ürün adı" if tr else "Produktname"
    )

    category = st.selectbox(
        "Kategori" if tr else "Kategorie",
        categories if tr else categories_de
    )

    col1, col2 = st.columns(2)

    with col1:
        price = st.number_input(
            "İlan fiyatı (€)" if tr else "Angebotspreis (€)",
            min_value=0.0,
            value=0.0
        )

    with col2:
        normal_price = st.number_input(
            "Normal piyasa fiyatı (€)" if tr else "Üblicher Marktpreis (€)",
            min_value=0.0,
            value=0.0
        )

    link = st.text_input(
        "İlan bağlantısı" if tr else "Anzeigen-Link"
    )

    submitted = st.form_submit_button(
        "İlanı hesapla ve ekle" if tr else "Berechnen und hinzufügen"
    )

    if submitted:
        if not name or price <= 0 or normal_price <= 0:
            st.error(
                "Ürün adı ve fiyatları gir." if tr
                else "Bitte Produktname und Preise eingeben."
            )
        else:
            discount = (normal_price - price) / normal_price * 100

            if discount >= minimum:
                st.session_state.offers.append({
                    "name": name,
                    "category": category,
                    "price": price,
                    "normal": normal_price,
                    "discount": discount,
                    "link": link
                })
                st.success(
                    "İlan eklendi!" if tr else "Angebot hinzugefügt!"
                )
            else:
                st.warning(
                    f"İndirim %{discount:.1f}. Minimum %{minimum} gerekli."
                    if tr else
                    f"Rabatt {discount:.1f}%. Mindestens {minimum}% erforderlich."
                )

st.divider()

st.subheader(
    "🔥 Bulunan fırsatlar" if tr else "🔥 Gefundene Angebote"
)

if not st.session_state.offers:
    st.info(
        "Henüz ilan yok. Yukarıdan ilan ekleyebilirsin."
        if tr else
        "Noch keine Angebote. Du kannst oben ein Angebot hinzufügen."
    )
else:
    for offer in reversed(st.session_state.offers):
        with st.container(border=True):
            st.markdown("### " + offer["name"])
            st.write(offer["category"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Fiyat", f'{offer["price"]:.2f} €')
            c2.metric(
                "Normal fiyat" if tr else "Marktpreis",
                f'{offer["normal"]:.2f} €'
            )
            c3.metric("İndirim" if tr else "Rabatt",
                      f'%{offer["discount"]:.1f}')

            if offer["link"].startswith(("https://", "http://")):
                st.link_button(
                    "İlanı aç" if tr else "Angebot öffnen",
                    offer["link"]
                )

st.divider()

st.caption(
    "KDH ilk sürüm • Gerçek zamanlı otomatik ilan taraması henüz bağlı değil."
    if tr else
    "KDH erste Version • Automatische Live-Anzeigensuche ist noch nicht verbunden."
)
