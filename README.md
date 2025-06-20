# 🌐 KAREL Network Dashboard - Fiber Arıza Takip Sistemi

## 🚀 Hızlı Başlangıç (TL;DR)

```bash
# 1. Klonla
git clone https://github.com/oceandi/extension-for-envanter
cd extension-for-envanter

# 2. Sanal ortam oluştur ve aktifle
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. Çalıştır (DB zaten mevcut)
python app.py

# 5. Tarayıcıda aç
http://localhost:5000
```

## 📋 Proje Özeti

KAREL Network Dashboard, fiber optik altyapı arızalarını ve network operasyonlarını takip etmek için geliştirilmiş kapsamlı bir yönetim sistemidir. Excel benzeri veri girişi, harita görselleştirmesi ve çoklu modül desteği ile network operasyonlarını kolaylaştırır.

## 🚀 Özellikler

### Ana Modül: Fiber Arıza Takibi
- 28 sütunlu detaylı arıza kaydı (14 input + 14 düzenlenebilir alan)
- Google Maps entegrasyonu ile arıza haritası
- KMZ export (Google Earth uyumlu)
- Excel import/export
- Inline editing (Excel gibi düzenleme)
- Gerçek zamanlı istatistikler

### Ek Modüller
1. **Deplase Islah Kablo Upgrade**
   - İş tipi takibi (DEPLASE, GÖMÜLÜ EK KUTUSU ISLAH, KABLO UPGRADE)
   - Koordinat bazlı takip
   
2. **Hasar Tazmin**
   - Firma ve taşeron takibi
   - Muhaberat yönetimi
   - Tarih bazlı takip

3. **FTTB Optimizasyon**
   - Ring ve lokasyon yönetimi
   - CI name takibi
   - Durum takibi (YAPILDI/YAPILMADI)

4. **Kritik Modernizasyon**
   - Bülten numarası ile takip
   - İş tipi ve lokasyon yönetimi

## 🛠 Teknoloji Stack

- **Backend**: Flask (Python)
- **Database**: SQLite + SQLAlchemy ORM
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **UI Framework**: Custom dark theme design
- **Maps**: Google Maps API
- **Charts**: Chart.js
- **File Processing**: pandas, openpyxl
- **Export**: simplekml (KMZ), xlsxwriter

## 📦 Kurulum

### 1. Gereksinimler
```bash
Python 3.12+
pip
venv (sanal ortam önerilir)
```

### 2. Sanal Ortam Oluşturun (Opsiyonel)
```bash
python -m venv venv
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

Eğer `requirements.txt` yoksa manuel olarak:
```bash
pip install flask flask-sqlalchemy flask-migrate pandas openpyxl simplekml xlsxwriter
```

### 4. Veritabanı Zaten Mevcut
Proje hazır bir veritabanı ile geliyor (`instance/fiberariza.db`). Yeni migration gerekirse:
```bash
flask db migrate -m "Açıklama"
flask db upgrade
```

### 5. Uygulamayı Başlatın
```bash
python app.py
```

Uygulama `http://localhost:5000` adresinde çalışacaktır.

## 📁 Proje Yapısı

```
extension-for-envanter/
├── README.md              # Bu dosya
├── app.py                 # Ana Flask uygulaması
├── requirements.txt       # Python bağımlılıkları
├── tree.py               # Proje yapısı görüntüleme
├── instance/
│   └── fiberariza.db     # SQLite veritabanı (28MB)
├── templates/            # HTML şablonları
│   ├── base.html         # Temel şablon
│   ├── dashboard.html    # Eski dashboard
│   ├── explorer.html     # Ana dashboard (Fiber Arızalar)
│   ├── edit.html         # Düzenleme sayfası
│   ├── index.html        # Ana sayfa
│   ├── deplase_islah.html
│   ├── hasar_tazmin.html
│   ├── fttb_optimizasyon.html
│   └── kritik_modernizasyon.html
├── static/               # Statik dosyalar (CSS, JS, img)
├── files/                # Kullanıcı yüklemeleri
├── xlsx/                 # Örnek Excel dosyaları
│   ├── import.xlsx       # İmport şablonu
│   ├── export.xlsx       # Export örneği
│   └── *.jpeg/jpg        # Ekran görüntüleri
├── migrations/           # Database migrations
│   └── versions/         # Migration geçmişi
└── __pycache__/         # Python cache (ignore)

## 🗄 Veritabanı Şeması

### FiberAriza Tablosu (Ana tablo - 28 sütun)
```sql
- id (Primary Key)
- hafta, bolge, bulten_no, il, guzergah, lokasyon
- ariza_baslangic, ariza_bitis
- ariza_konsolide, ariza_kok_neden
- hags_asildi_mi, refakat_durumu, servis_etkisi, ariza_suresi
- kordinat_a, kordinat_b (Koordinatlar)
- serivs_etkisi, kablo_tipi
- hags_suresi, kesinti_suresi
- kalici_cozum, kullanilan_malzeme, aciklama
```

### DeplaseIslah Tablosu
```sql
- id, yil, hafta, ddo, guzergah
- is_tipi (DEPLASE/GÖMÜLÜ EK KUTUSU ISLAH/KABLO UPGRADE)
- kordinat_a, kordinat_b, aciklama
- durum (TAMAMLANDI/DEVAM EDİYOR)
```

### HasarTazmin Tablosu
```sql
- id, bolge, yazi_no, tarih, asil_firma
- muhaberat_verilis_tarihi, taseron
- durumu (FİRMAYA İLETİLDİ/HASAR TAZMİN HAZIRLANIYOR)
- muhaberat_teslim_eden
```

### FTTBOptimizasyon Tablosu
```sql
- id, yil, hafta, ddo, statu, obek
- fttb_ring_name, lokasyon_id, ci_name
- aciklama, durum (YAPILDI/YAPILMADI)
```

### KritikModernizasyon Tablosu
```sql
- id, yil, hafta, ddo, bulten_no
- lokasyon_id, is_tipi, lokasyon
- aciklama, durumu (TAMAMLANDI/DEVAM EDİYOR)
```

## 🎯 Kullanım

### Excel Import
1. İlgili sekmeye gidin
2. "Import" butonuna tıklayın
3. Excel dosyanızı sürükleyin veya seçin
4. Otomatik olarak veritabanına aktarılır

### Inline Editing
1. Tabloda herhangi bir satırın düzenle butonuna tıklayın
2. Hücreleri doğrudan düzenleyin
3. Yeşil onay butonuna tıklayın

### Harita Görünümü
1. Dashboard'da "Harita Görünümü" linkine tıklayın
2. Koordinatlı arızalar haritada görüntülenir
3. Yeşil: Çözülen, Kırmızı: Çözülmeyen

### Export İşlemleri
- **Excel Export**: Her modülde "Export" butonu
- **KMZ Export**: Ana dashboard'da dropdown menüden
  - Tüm arızalar
  - Sadece çözülenler
  - Sadece çözülmeyenler

## 🔧 API Endpoints

### Fiber Arıza API'leri
- `GET /api/arizalar` - Tüm arızaları getir
- `POST /api/ariza` - Yeni arıza ekle
- `PUT /api/ariza/<id>` - Arıza güncelle
- `DELETE /api/ariza/<id>` - Arıza sil
- `GET /api/map_data` - Harita verileri

### Diğer Modül API'leri
- `/api/deplase_islah`
- `/api/hasar_tazmin`
- `/api/fttb_optimizasyon`
- `/api/kritik_modernizasyon`

Her API CRUD işlemlerini destekler.

## 🎨 Özelleştirme

### Renk Teması
CSS değişkenleri ile kolayca özelleştirilebilir:
```css
:root {
    --primary-color: #1e3a8a;
    --secondary-color: #2563eb;
    --accent-color: #3b82f6;
    --success-color: #22c55e;
    --warning-color: #f59e0b;
    --danger-color: #ef4444;
}
```

### Google Maps API Key
`explorer.html` içinde kendi API key'inizi kullanın:
```javascript
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY"></script>
```
**Mevcut Key**: `AIzaSyANpGORy7eoWhHRnWBLxScytWpj1Xegsz8` (Değiştirmeniz önerilir)

## 🚧 Gelecek Özellikler

- [ ] Kullanıcı yetkilendirme sistemi
- [ ] Raporlama modülü
- [ ] Mobil uygulama
- [ ] Real-time bildirimler
- [ ] AI destekli arıza tahmini
- [ ] Hologram asistan entegrasyonu

## 📝 Notlar

- Veritabanı `instance/fiberariza.db` konumunda tutulur (mevcut: ~28MB)
- Tüm tarihler Türkçe formatında görüntülenir
- Excel import sırasında sütun isimleri tam olarak eşleşmelidir
- Koordinatlar ondalık format kullanır (40.123456, 29.123456)
- `xlsx/` klasöründe örnek import/export dosyaları bulunur
- Migration geçmişi `migrations/versions/` altında saklanır

## 🎁 Örnek Dosyalar

`xlsx/` klasöründe bulunan dosyalar:
- `import.xlsx` - Import için örnek Excel şablonu
- `export.xlsx` - Export edilmiş örnek veri
- `.jpeg/.jpg` dosyaları - Uygulama ekran görüntüleri

## ⚠️ Önemli Bilgiler

1. **Veritabanı Yedekleme**: `instance/fiberariza.db` dosyasını düzenli yedekleyin
2. **Migration Uyarısı**: Yeni migration oluştururken mevcut verileri kontrol edin
3. **Excel Format**: Import edilecek Excel dosyaları belirtilen sütun isimlerini içermelidir
4. **Koordinat Formatı**: Enlem ve boylam değerleri ondalık sayı formatında olmalıdır

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Push edin (`git push origin feature/AmazingFeature`)
5. Pull Request açın

## 📄 Lisans

Bu proje şirket içi kullanım için geliştirilmiştir.

## 👥 İletişim

Proje Geliştirici: [Ahmet Emirhan Korkmaz]
E-posta: [korkmaz.x7@gmail.com]

## 🔄 Migration Geçmişi

Projede mevcut migration'lar:
1. `08066cbaeb1a` - İlk tablo
2. `05b48e04ce5f` - serivs_etkisi eklendi
3. `285364aa2f6e` - Add DeplaseIslah table
4. `72049cfd249a` - Add DeplaseIslah and HasarTazmin tables
5. `adc38353a02e` - Add DeplaseIslah, HasarTazmin and...
6. `82bbb423f4cc` - Add all new tables (Final)

---

**Proje Durumu**: ✅ Tamamlandı ve çalışır durumda
**Son Güncelleme**: Haziran 2025
**Versiyon**: 1.0