# 🚀 SEO-Pulse

**Profesyonel Web Performans İzleme ve Rekabet Analizi Aracı**

SEO-Pulse, web sitelerinizin performansını Google PageSpeed Insights API ile analiz eder, rakiplerinizle karşılaştırır ve otomatik raporlar gönderir.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Supabase](https://img.shields.io/badge/Database-Supabase-dark.svg)

---

## ✨ Özellikler

| Özellik | Açıklama |
|---------|----------|
| 📊 **Performans Analizi** | Google PageSpeed Insights API ile mobil performans skorları |
| 🏁 **Rakip Karşılaştırması** | Birden fazla rakibi takip et, kimin önde olduğunu gör |
| 📈 **LCP & CLS Takibi** | Core Web Vitals metriklerini izle |
| 🤖 **Zeki Tavsiye Sistemi** | Türkçe açıklamalarla actionable öneriler |
| 📧 **Otomatik E-posta Raporları** | Profesyonel formatta günlük/haftalık raporlar |
| 🗄️ **Supabase Entegrasyonu** | Tüm veriler bulutta güvenle saklanır |
| ⏰ **GitHub Actions Desteği** | Zamanlı otomatik çalıştırma |

---

## 📸 Ekran Görüntüleri

### Terminal Çıktısı
```
────────────────────────────────────────────────────────────
[14:04:21] ℹ️  SEO-Pulse v2.0 başlatılıyor...
────────────────────────────────────────────────────────────
[14:04:21] ✅ Supabase bağlantısı kuruldu
[14:04:21] ℹ️  10 site bulundu
────────────────────────────────────────────────────────────
[14:04:21] ℹ️  [1/10] Benim Sitem
[14:04:21] → Taranıyor: https://example.com
[14:05:00] ✅ Analiz tamamlandı: 85/100 | LCP: 2.3s | CLS: 0.05
[14:05:00] ✅ Veritabanına kaydedildi (ID: 42)
```

### E-posta Raporu Örneği
```
╔══════════════════════════════════════════════════════════╗
║              🚀 SEO-PULSE PERFORMANS RAPORU               ║
╠══════════════════════════════════════════════════════════╣
║ 📊 SİTEMİZ                                                ║
║    Performance: 85/100 | LCP: 2.3s | CLS: 0.05           ║
╠══════════════════════════════════════════════════════════╣
║ 🏁 RAKİP KARŞILAŞTIRMASI                                  ║
║    ✅ Rakip A → 78 puan (7 puan gerideler)                ║
║    ⚠️  Rakip B → 92 puan (7 puan ÖNDEler!)                ║
╠══════════════════════════════════════════════════════════╣
║ 📋 YAPILMASI GEREKENLER                                   ║
║    🔴 1. Kullanılmayan JavaScript'i Kaldırın              ║
║       Potansiyel Kazanç: [Est savings of 289 KiB]        ║
╚══════════════════════════════════════════════════════════╝
```

---

## 🛠️ Kurulum

### 1. Depoyu Klonla
```bash
git clone https://github.com/enqinsel/seo-pulse.git
cd seo-pulse
```

### 2. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 3. Ortam Değişkenlerini Ayarla
`.env.example` dosyasını `.env` olarak kopyala ve doldur:

```bash
cp .env.example .env
```

```env
# Google PageSpeed Insights API Key
# https://developers.google.com/speed/docs/insights/v5/get-started
PAGESPEED_API_KEY=your_api_key_here

# Supabase Credentials
# https://supabase.com/dashboard
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Email (Gmail App Password)
# https://myaccount.google.com/apppasswords
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### 4. Veritabanı Tablolarını Oluştur
Supabase SQL Editor'da:

```sql
-- Sites tablosu
CREATE TABLE sites (
  id SERIAL PRIMARY KEY,
  site_url TEXT NOT NULL,
  label TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Speed logs tablosu
CREATE TABLE speed_logs (
  id SERIAL PRIMARY KEY,
  site_id INTEGER REFERENCES sites(id),
  performance_score INTEGER,
  lcp_speed FLOAT,
  cls_score FLOAT,
  recommendations JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Örnek site ekle
INSERT INTO sites (site_url, label) VALUES 
  ('https://your-site.com', 'Benim Sitem'),
  ('https://competitor1.com', 'Rakip 1'),
  ('https://competitor2.com', 'Rakip 2');
```

---

## 🚀 Kullanım

### Manuel Çalıştırma
```bash
python main.py
```

### GitHub Actions ile Otomatik (Haftalık)
Workflow dosyası `.github/workflows/weekly_report.yml` içinde yapılandırılmıştır.
Her **Pazartesi 09:00 (UTC+3)** otomatik çalışır.

**GitHub Secrets olarak ekle:**
- `PAGESPEED_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `EMAIL_SENDER`
- `EMAIL_PASSWORD`

---

## 📁 Proje Yapısı

```
seo-pulse/
├── main.py              # Ana uygulama
├── requirements.txt     # Bağımlılıklar
├── .env.example         # Örnek ortam değişkenleri
├── .gitignore           # Git hariç tutulanlar
├── README.md            # Bu dosya
└── .github/
    └── workflows/
        └── weekly_report.yml  # GitHub Actions
```

---

## 🔧 Teknik Detaylar

- **Python 3.9+**
- **Google PageSpeed Insights API v5** (Mobile strategy)
- **Supabase** (PostgreSQL)
- **SMTP** (Gmail)

### Desteklenen Metrikler
- Performance Score (0-100)
- LCP (Largest Contentful Paint) - saniye
- CLS (Cumulative Layout Shift) - skor

---

## 📝 Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

---

## 📬 İletişim

**Geliştirici:** [@enqinsel](https://github.com/enqinsel)

---

<p align="center">
  <b>⭐ Bu proje işinize yaradıysa yıldız vermeyi unutmayın!</b>
</p>
