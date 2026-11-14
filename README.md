# Kleinanzeigen Deal Hunter

Velbert merkezli 50 km çevredeki fırsatları izlemek için Türkçe web uygulaması başlangıç projesi.

## Çalıştırma

Python 3.10+ önerilir.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Tarayıcıda Streamlit'in verdiği yerel adresi açın (genellikle http://localhost:8501).

## Özellikler
- Fırsat paneli ve indirim filtreleri
- Velbert merkezli 50 km mesafe filtresi (ilan koordinatı sağlanırsa)
- İlanı manuel ekleme
- CSV ile toplu içe aktarma
- Piyasa fiyatına göre indirim ve tasarruf farkı hesaplama
- İzinli veri sağlayıcısı için API adaptörü
- SQLite kalıcı kayıt

## Gerçek otomatik tarama
Kleinanzeigen'in kullanım koşulları otomatik crawler/scraper kullanımını kısıtlar. Bu proje siteyi izinsiz kazımaz. Otomatik tarama için kullanım koşullarına uygun yetkili bir veri sağlayıcısı/API bağlantısı gerekir.

`.env.example` dosyasını `.env` olarak kopyalayıp `AUTHORIZED_LISTINGS_API_URL` ve `AUTHORIZED_LISTINGS_API_TOKEN` değerlerini sağlayıcınızdan alın. API, `listings` dizisi içinde en az `title`, `price`, `market_price` alanlarını döndürmelidir. Diğer alanlar isteğe bağlıdır.

## Yayına alma
Bu proje kaynak kodudur; henüz internette barındırılmıyor. Streamlit Community Cloud, Render veya kendi sunucunuzda yayınlanabilir. Yayın öncesi kalıcı disk/SQLite saklama, erişim koruması, gizli anahtar yönetimi ve sağlayıcı kullanım izinleri yapılandırılmalıdır.
