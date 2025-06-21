## 🤖 AI/ML Entegrasyonu

### Mevcut Durum
- ✅ Ollama kurulu ve çalışıyor
- ✅ DeepSeek-R1:7b modeli indirildi ve test edildi
- ✅ Local AI setup scripti hazır (`local_ai_setup.py`)
- ✅ ML veri hazırlama scripti hazır (`db_analyzer.py`)
- ✅ Training data JSONL formatında (`ml_data/training_data.jsonl`)

### AI Kullanımı

#### 1. Model Çalıştırma
```bash
# Terminal 1: Ollama servisini başlat
ollama serve

# Terminal 2: İnteraktif analiz
python local_ai_setup.py
## 🌐 KAREL Network Dashboard - Fiber Arıza Takip Sistemi

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

## 🤖 AI/ML Entegrasyonu

### ✅ Mevcut Durum (Ocak 2025)
- ✅ Ollama kurulu ve çalışıyor
- ✅ DeepSeek-R1:7b modeli indirildi ve test edildi
- ✅ Local AI setup scripti hazır (`local_ai_setup.py`)
- ✅ ML veri hazırlama scripti hazır (`db_analyzer.py`)
- ✅ Training data genişletme scripti hazır (`generate_training_data.py`)
- ✅ Training data JSONL formatında (`ml_data/enhanced_training_data.jsonl`)
- ⚠️ Terminal'de çalışıyor, web entegrasyonu bekliyor
- 🔄 RAG sistemi kurulum aşamasında

### 🎯 Aktif Çalışmalar

#### RAG (Retrieval Augmented Generation) vs Fine-tuning
**RAG Avantajları:**
- ✅ Hemen kullanıma hazır (fine-tuning gerektirmez)
- ✅ Güncel veri ile çalışır (veritabanı değişikliklerini anında yansıtır)
- ✅ Daha az kaynak kullanır
- ✅ Hallüsinasyon riski düşük

**RAG Kurulumu (Devam Eden):**
```bash
# 1. Vector DB kurulumu
pip install chromadb langchain

# 2. RAG pipeline (yakında eklenecek)
python setup_rag.py

# 3. Web entegrasyonu
# app.py'ye AI route'ları eklenecek
```

### 🚀 Hızlı Başlangıç

#### Terminal'de AI Kullanımı (Çalışıyor ✅)
```bash
# Terminal 1: Ollama servisini başlat
ollama serve

# Terminal 2: İnteraktif analiz
python local_ai_setup.py
# Seçim: 3 (otomatik deepseek-r1:7b kullanır)
```

#### Web Arayüzünde AI (Yapılacak 🔄)
```python
# app.py'ye eklenecek basit entegrasyon
from ai_config import AI_CONFIG
import requests

@app.route('/api/ai/quick_analysis', methods=['POST'])
def quick_ai_analysis():
    prompt = request.json.get('prompt', '')
    # Basit Ollama çağrısı
    response = requests.post(
        f"{AI_CONFIG['ollama_url']}/api/generate",
        json={"model": AI_CONFIG['model'], "prompt": prompt, "stream": False}
    )
    return jsonify({"response": response.json().get('response', '')})
```

### 📝 Kritik Notlar (Yeni Chat için)

**1. Model Durumu:**
- Model: `deepseek-r1:7b` 
- Problem: Fiber terminolojisini bilmiyor (HAGS'ı yanlış anlıyor)
- Çözüm: RAG sistemi kurulacak

**2. Dosya Konumları:**
- `local_ai_setup.py` - Ana AI script (7b varsayılan)
- `generate_training_data.py` - 100 Q&A üretir
- `ai_config.py` - Merkezi config
- `ml_data/` - Tüm ML verileri

**3. Test Komutları:**
```bash
# AI bağlantı testi
python ai_config.py

# Training data üret
python generate_training_data.py

# Interaktif test
python local_ai_setup.py
```

### 🎮 Gelecek: Kullanıcı Playground (Konsept)

Kullanıcıların kendi modüllerini ekleyebileceği sistem:
```python
# Veritabanı modeli
class UserModule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    module_name = db.Column(db.String(100))
    icon = db.Column(db.String(50))
    route = db.Column(db.String(100))
    table_schema = db.Column(db.JSON)  # Dinamik tablo yapısı
    created_at = db.Column(db.DateTime)

# Dinamik route oluşturma
@app.route('/playground/<module_name>')
def user_module(module_name):
    module = UserModule.query.filter_by(module_name=module_name).first_or_404()
    return render_template('playground.html', module=module)
```

### ⚡ Acil Yapılacaklar (Öncelik Sırası)

1. **Web AI Entegrasyonu** (1-2 saat)
   - Basit API endpoint
   - Frontend'de test butonu
   
2. **RAG Kurulumu** (2-3 saat)
   - ChromaDB setup
   - Fiber dokümantasyon yükleme
   - Query pipeline

3. **Dashboard AI Widget** (1 saat)
   - Mevcut `ai_frontend_widget` kodunu entegre et

---

**Son Güncelleme**: Ocak 2025
**Aktif Branch**: main
**Kritik**: RAG > Fine-tuning (hız ve pratiklik açısından)

## 🚀 Gelecek Adımlar (Roadmap)

### 1. Fine-tuning (Kısa Vade - 1-2 Hafta)
Fine-tuning ile model fiber arıza konusunda uzmanlaşacak:

```bash
# Adım 1: Training verisi hazır
ml_data/training_data.jsonl  # 3 örnek mevcut, daha fazla eklenecek

# Adım 2: Fine-tuning araçları
pip install ollama-finetune  # (Yakında)
# veya
pip install transformers datasets  # Hugging Face yöntemi

# Adım 3: Model eğitimi
python finetune_model.py \
  --base_model deepseek-r1:7b \
  --data ml_data/training_data.jsonl \
  --output models/fiber_expert_v1

# Adım 4: Test ve deployment
ollama create fiber-expert -f ./Modelfile
ollama run fiber-expert
```

**Fine-tuning Veri Hazırlığı:**
- Her arıza kaydı için soru-cevap çiftleri
- Türkçe fiber terminolojisi sözlüğü
- Çözüm önerileri veritabanı
- HAGS, FTTB, DDO gibi terimlerin açıklamaları

### 2. Hologram Entegrasyonu (Orta Vade - 3-6 Ay)

#### Faz 1: Avatar Sistemi
```csharp
// Unity3D Projesi Yapısı
FiberAssistant/
├── Assets/
│   ├── Scripts/
│   │   ├── AIConnector.cs      # Ollama bağlantısı
│   │   ├── AvatarController.cs # 3D karakter kontrolü
│   │   └── VoiceSynthesis.cs   # TTS entegrasyonu
│   ├── Models/
│   │   └── TechnicianAvatar.fbx # 3D model
│   └── Animations/
│       ├── Idle.anim
│       ├── Talking.anim
│       └── Gestures.anim
```

#### Faz 2: Ses Sentezi
```python
# Türkçe TTS entegrasyonu
# Seçenek 1: Coqui TTS
from TTS.api import TTS
tts = TTS("tts_models/tr/common-voice/glow-tts")
tts.tts_to_file(text=ai_response, file_path="output.wav")

# Seçenek 2: Azure Neural TTS
# Daha doğal Türkçe ses
```

#### Faz 3: Hologram Display
- **Hardware**: Looking Glass Portrait veya HoloLens 2
- **Software**: Unity Holographic Remoting
- **Interaction**: El hareketleri, ses komutları

```python
# Hologram kontrol API'si
@app.route('/api/hologram/speak', methods=['POST'])
def hologram_speak():
    text = request.json['text']
    # 1. AI'dan yanıt al
    ai_response = get_ai_response(text)
    # 2. TTS ile sese çevir
    audio_file = generate_speech(ai_response)
    # 3. Unity'ye gönder
    send_to_unity(audio_file, ai_response)
    return jsonify({"status": "speaking"})
```

### 3. Türkiye Geneli Analiz (Uzun Vade - 6-12 Ay)

#### Veri Toplama Stratejisi
```python
# Tüm illerin fiber altyapı verisi
turkey_fiber_data = {
    "istanbul": {
        "total_km": 50000,
        "failure_rate": 0.02,
        "critical_points": [...],
    },
    "ankara": {...},
    "izmir": {...},
    # ... 81 il
}

# AI tahmin modeli
class TurkeyFiberPredictor:
    def predict_national_risks(self):
        """Ulusal risk haritası oluştur"""
        pass
    
    def investment_recommendations(self):
        """Yatırım önceliklendirmesi"""
        pass
    
    def seasonal_analysis(self):
        """Mevsimsel arıza tahminleri"""
        pass
```

#### Ulusal Dashboard
```javascript
// Türkiye haritası üzerinde risk görselleştirme
const riskMap = new TurkeyRiskMap({
    data: nationalFiberData,
    layers: [
        'failure_density',      // Arıza yoğunluğu
        'investment_priority',  // Yatırım önceliği
        'weather_impact',       // Hava durumu etkisi
        'earthquake_risk'       // Deprem riski
    ]
});
```

#### Analiz Çıktıları
1. **Risk Haritası**
   - İl bazında arıza riski skorları
   - Kritik altyapı noktaları
   - Öncelikli müdahale bölgeleri

2. **Yatırım Önerileri**
   - ROI hesaplamaları
   - Bütçe dağılımı önerileri
   - Ekip yerleşim planı

3. **Tahmine Dayalı Bakım**
   - 30-60-90 günlük arıza tahminleri
   - Mevsimsel hazırlık planları
   - Malzeme stok optimizasyonu

### 4. Model İyileştirme Önerileri

#### Mevcut Model Performansı
DeepSeek-R1:7b şu an temel sorulara yanıt verebiliyor ancak:
- ❌ HAGS terimini yanlış anlıyor
- ❌ Türkçe çıktıda tutarsızlıklar var
- ❌ Fiber terminolojisine hakim değil

#### İyileştirme Planı
```bash
# 1. Daha fazla training verisi
python generate_training_data.py --count 1000

# 2. Türkçe optimize model
ollama pull qwen2.5:7b-instruct  # Alternatif

# 3. RAG (Retrieval Augmented Generation)
python setup_vector_db.py  # Fiber dokümantasyon DB'si
```

### 5. Entegrasyon Timeline

```mermaid
gantt
    title AI/ML Entegrasyon Roadmap
    dateFormat  YYYY-MM-DD
    section Fine-tuning
    Training Data Hazırlama     :2025-01-20, 7d
    Model Eğitimi              :7d
    Test ve Optimizasyon       :7d
    
    section Hologram
    Unity Proje Setup          :2025-02-10, 14d
    Avatar Geliştirme          :21d
    TTS Entegrasyonu           :14d
    Hardware Test              :14d
    
    section Türkiye Analizi
    Veri Toplama               :2025-04-01, 60d
    Model Geliştirme           :45d
    Dashboard Entegrasyonu     :30d
    Pilot Test                 :30d
```

## 📚 AI/ML Kaynaklar

- **Model**: [DeepSeek-R1 Dokümantasyon](https://github.com/deepseek-ai/DeepSeek-R1)
- **Ollama**: [Ollama.ai](https://ollama.ai)
- **Unity Hologram**: [Mixed Reality Toolkit](https://github.com/microsoft/MixedRealityToolkit-Unity)
- **Türkçe TTS**: [Coqui TTS](https://github.com/coqui-ai/TTS)

---

**AI Durumu**: 🟡 Geliştirme aşamasında
**Model**: DeepSeek-R1:7b
**Sonraki Adım**: Fine-tuning verisi genişletme

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

Proje Geliştirici: Ahmet Emirhan Korkmaz
E-posta: korkmaz.x7@gmail.com

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
**Son Güncelleme**: Ocak 2025
**Versiyon**: 1.0