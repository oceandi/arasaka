#!/usr/bin/env python3
"""
KAREL Network Dashboard - Training Data Genişletme
Fiber arıza veritabanından daha fazla training örneği üretir
"""

import json
import sqlite3
import pandas as pd
from datetime import datetime
import random

class TrainingDataGenerator:
    def __init__(self, db_path: str = 'instance/fiberariza.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
        # Fiber terminolojisi sözlüğü
        self.terminology = {
            "HAGS": "Hizmet Alım Garanti Süresi - Arızanın çözülmesi gereken maksimum süre",
            "FTTB": "Fiber To The Building - Binaya kadar fiber altyapı",
            "DDO": "Dış Dağıtım Odası - Fiber dağıtım noktası",
            "OTDR": "Optical Time Domain Reflectometer - Fiber kablo test cihazı",
            "Ek Kutusu": "Fiber kabloların birleştirildiği bağlantı noktası",
            "Deplase": "Fiber kablo güzergahının değiştirilmesi",
            "Refakat": "Arıza giderme sırasında diğer kurumlarla koordinasyon"
        }
        
        # Çözüm önerileri
        self.solutions = {
            "TC Karayolları Çalışması": [
                "Karayolları ile koordinasyon toplantısı yapın",
                "Çalışma öncesi fiber güzergahlarını paylaşın",
                "Kritik noktalara uyarı levhaları yerleştirin",
                "Alternatif güzergah planlaması yapın"
            ],
            "Doğalgaz Firması Çalışması": [
                "Doğalgaz firması ile ortak çalışma protokolü oluşturun",
                "Kazı öncesi fiber haritasını paylaşın",
                "Kritik hatlara koruma borusu takın",
                "Refakat ekibi görevlendirin"
            ],
            "Kablo Kopması": [
                "Yedek fiber hazır bulundurun",
                "Ek kutusu lokasyonlarını güncelleyin",
                "OTDR ile düzenli test yapın",
                "Kritik hatlara yedekli altyapı kurun"
            ],
            "Ek Kutusu Arızası": [
                "Ek kutularını periyodik kontrol edin",
                "Nem ve su izolasyonunu güçlendirin",
                "Yedek ek kutusu bulundurun",
                "Termal kamera ile kontrol yapın"
            ]
        }
        
    def generate_qa_pairs(self, count: int = 100):
        """Soru-cevap çiftleri üret"""
        training_data = []
        
        # Veritabanından gerçek arızaları çek
        df = pd.read_sql_query("SELECT * FROM fiber_ariza", self.conn)
        
        # 1. Genel sorular
        general_questions = [
            "HAGS nedir ve neden önemlidir?",
            "Fiber arıza takibinde dikkat edilmesi gerekenler nelerdir?",
            "FTTB altyapısında en sık karşılaşılan sorunlar nelerdir?",
            "Koordinat bilgisi neden önemlidir?",
            "Kalıcı çözüm nasıl sağlanır?"
        ]
        
        for q in general_questions:
            training_data.append(self._create_general_qa(q))
        
        # 2. Veritabanı bazlı sorular
        for _, row in df.iterrows():
            # Arıza analizi soruları
            if pd.notna(row.get('ariza_kok_neden')):
                training_data.append(self._create_failure_analysis_qa(row))
            
            # HAGS soruları
            if row.get('hags_asildi_mi') == 'Evet':
                training_data.append(self._create_hags_qa(row))
            
            # Çözüm soruları
            if row.get('kalici_cozum') == 'Hayır':
                training_data.append(self._create_solution_qa(row))
        
        # 3. Tahmin soruları
        risk_areas = df['bolge'].value_counts().head(3).index.tolist()
        for area in risk_areas:
            training_data.append(self._create_prediction_qa(area, df))
        
        # 4. Karşılaştırma soruları
        if len(df['bolge'].unique()) > 1:
            training_data.extend(self._create_comparison_qa(df))
        
        # Karıştır ve sınırla
        random.shuffle(training_data)
        return training_data[:count]
    
    def _create_general_qa(self, question: str):
        """Genel soru-cevap çifti oluştur"""
        answers = {
            "HAGS nedir ve neden önemlidir?": f"""
HAGS (Hizmet Alım Garanti Süresi), fiber arızalarının çözülmesi için belirlenen maksimum süredir. 

Önemi:
1. **Müşteri Memnuniyeti**: HAGS aşımı müşteri şikayetlerine yol açar
2. **Cezai Yaptırım**: Aşım durumunda maddi cezalar uygulanabilir
3. **Performans Göstergesi**: Ekip verimliliğini ölçer
4. **SLA Uyumu**: Servis seviyesi anlaşmalarına uyum sağlar

HAGS aşımını önlemek için:
- Ekip sayısını artırın
- Yedek malzeme bulundurun
- Öncelikli arızaları belirleyin
- Coğrafi dağılımı optimize edin
""",
            "Fiber arıza takibinde dikkat edilmesi gerekenler nelerdir?": """
Fiber arıza takibinde kritik noktalar:

1. **Doğru Kayıt**:
   - Koordinatları mutlaka girin
   - Arıza nedenini detaylı yazın
   - Başlangıç/bitiş saatlerini doğru kaydedin

2. **Hızlı Müdahale**:
   - HAGS süresini takip edin
   - Kritik lokasyonlara öncelik verin
   - Yedek ekip hazır bulundurun

3. **Kalıcı Çözüm**:
   - Geçici çözümlerle yetinmeyin
   - Kök nedeni tespit edin
   - Önleyici tedbirler alın

4. **Dokümantasyon**:
   - Kullanılan malzemeleri kaydedin
   - Fotoğraf/OTDR ölçümü ekleyin
   - Refakat durumunu belirtin
"""
        }
        
        return {
            "messages": [
                {"role": "system", "content": "Sen Türkiye fiber optik altyapı uzmanısın. Detaylı ve pratik bilgiler veriyorsun."},
                {"role": "user", "content": question},
                {"role": "assistant", "content": answers.get(question, "Bu konuda detaylı bilgi için dokümantasyona bakınız.")}
            ]
        }
    
    def _create_failure_analysis_qa(self, row):
        """Arıza analizi soru-cevabı"""
        root_cause = row.get('ariza_kok_neden', 'Bilinmiyor')
        solutions = self.solutions.get(root_cause, ["Detaylı analiz yapın", "Uzman ekip gönderin"])
        
        return {
            "messages": [
                {"role": "system", "content": "Sen fiber arıza analiz uzmanısın. Kök neden analizi ve çözüm önerileri sunuyorsun."},
                {"role": "user", "content": f"{row.get('bolge')} bölgesinde {root_cause} kaynaklı arıza var. Ne önerirsin?"},
                {"role": "assistant", "content": f"""
{root_cause} kaynaklı arıza analizi:

🔍 **Durum Değerlendirmesi**:
- Bölge: {row.get('bolge')}
- İl: {row.get('il')}
- Lokasyon: {row.get('lokasyon', 'Belirtilmemiş')}
- Mevcut Durum: {'Çözüldü' if row.get('kalici_cozum') == 'Evet' else 'Devam ediyor'}

📋 **Önerilen Aksiyonlar**:
{chr(10).join(f'{i+1}. {solution}' for i, solution in enumerate(solutions[:3]))}

⚡ **Acil Müdahale**:
- OTDR ölçümü alın
- Yedek fiber hazırlayın
- Refakat gerekiyorsa koordine edin

🛡️ **Önleyici Tedbirler**:
- Benzer arızaları önlemek için {root_cause} risk haritası oluşturun
- Aylık kontrol planı hazırlayın
- Kritik noktalara sensör yerleştirin
"""}
            ]
        }
    
    def _create_hags_qa(self, row):
        """HAGS aşımı soru-cevabı"""
        return {
            "messages": [
                {"role": "system", "content": "HAGS yönetimi konusunda uzmansın. Süre aşımlarını analiz edip çözüm öneriyorsun."},
                {"role": "user", "content": f"{row.get('bolge')} bölgesinde HAGS aşımı var. Süre: {row.get('ariza_suresi')}. Ne yapmalıyız?"},
                {"role": "assistant", "content": f"""
⚠️ **HAGS Aşım Analizi**:

📊 **Mevcut Durum**:
- Bölge: {row.get('bolge')}
- Arıza Süresi: {row.get('ariza_suresi', 'Belirtilmemiş')}
- HAGS Durumu: AŞILDI
- Servis Etkisi: {row.get('servis_etkisi', 'Var')}

🚨 **Acil Eylem Planı**:
1. **Ekip Takviyesi**: En yakın yedek ekibi bölgeye yönlendirin
2. **Malzeme Kontrolü**: Gerekli malzemeler hazır mı kontrol edin
3. **Müşteri İletişimi**: Etkilenen müşterileri bilgilendirin
4. **Üst Yönetim**: Durum raporunu iletin

💡 **Çözüm Stratejisi**:
- Arıza tipine göre uzman ekip gönderin
- Paralel çalışma ile süreyi kısaltın
- Geçici çözüm uygulayıp kalıcı çözüm planlayın

📈 **İyileştirme Önerileri**:
- Bu bölgeye ekip sayısını artırın
- Kritik yedek malzeme deposu kurun
- Otomatik HAGS uyarı sistemi kurun
- Haftalık HAGS performans toplantısı yapın
"""}
            ]
        }
    
    def _create_solution_qa(self, row):
        """Çözüm önerisi soru-cevabı"""
        return {
            "messages": [
                {"role": "system", "content": "Fiber arıza çözüm uzmanısın. Kalıcı ve etkili çözümler öneriyorsun."},
                {"role": "user", "content": f"{row.get('il')} ilinde çözülmemiş arıza var. Kök neden: {row.get('ariza_kok_neden')}. Kalıcı çözüm?"},
                {"role": "assistant", "content": f"""
🔧 **Kalıcı Çözüm Planı**:

📍 **Arıza Detayları**:
- İl/Bölge: {row.get('il')} / {row.get('bolge')}
- Kök Neden: {row.get('ariza_kok_neden', 'Tespit edilmeli')}
- Güzergah: {row.get('guzergah', 'Belirtilmemiş')}

✅ **Kalıcı Çözüm Adımları**:

1. **Detaylı Analiz**:
   - OTDR ile hat testi yapın
   - Fiziksel kontrol gerçekleştirin
   - Çevresel faktörleri değerlendirin

2. **Teknik Müdahale**:
   - {'Hasarlı fiber değişimi' if 'kopma' in str(row.get('ariza_kok_neden', '')).lower() else 'Ek kutusu yenileme'}
   - Koruma borusu takılması
   - Güzergah optimizasyonu

3. **Altyapı İyileştirme**:
   - Kritik noktalara yedekleme
   - Sensör ve alarm sistemi
   - Periyodik bakım planı

4. **Dokümantasyon**:
   - As-built çizim güncelleme
   - Risk haritasına işleme
   - Bakım takvimi oluşturma

⏰ **Tahmini Süre**: 2-4 saat
💰 **Maliyet**: Orta (10-20K TL)
🎯 **Başarı Oranı**: %95+
"""}
            ]
        }
    
    def _create_prediction_qa(self, area, df):
        """Tahmin soruları"""
        area_failures = df[df['bolge'] == area]
        failure_count = len(area_failures)
        common_cause = area_failures['ariza_kok_neden'].mode()[0] if len(area_failures) > 0 else "Bilinmiyor"
        
        return {
            "messages": [
                {"role": "system", "content": "Fiber arıza tahmin uzmanısın. Geçmiş verilere dayalı risk analizi yapıyorsun."},
                {"role": "user", "content": f"{area} bölgesi için risk analizi yapar mısın?"},
                {"role": "assistant", "content": f"""
📊 **{area} Bölgesi Risk Analizi**:

📈 **Geçmiş Veri Analizi**:
- Toplam Arıza: {failure_count}
- En Sık Neden: {common_cause}
- HAGS Aşım Oranı: {(area_failures['hags_asildi_mi'] == 'Evet').sum() / len(area_failures) * 100 if len(area_failures) > 0 else 0:.1f}%

⚠️ **Risk Değerlendirmesi**:
- Risk Seviyesi: {'YÜKSEK' if failure_count > 5 else 'ORTA' if failure_count > 2 else 'DÜŞÜK'}
- Kritik Faktörler:
  • {common_cause} riski devam ediyor
  • Bölgesel altyapı yaşı
  • Çevresel faktörler (inşaat, kazı vb.)

🔮 **30 Günlük Tahmin**:
- Beklenen Arıza: {int(failure_count * 0.3)} - {int(failure_count * 0.5)}
- Yüksek Risk Günleri: Pazartesi-Salı (inşaat aktivitesi)
- HAGS Risk: {'Yüksek' if failure_count > 3 else 'Orta'}

🛡️ **Önleyici Tedbirler**:
1. **Proaktif Kontrol**: Haftada 2 kez saha kontrolü
2. **Ekip Hazırlığı**: 1 ekip sürekli hazır
3. **Malzeme Stoku**: {common_cause} için yedek malzeme
4. **İletişim**: İlgili kurumlarla haftalık koordinasyon

💡 **Yatırım Önerisi**:
- Öncelik: {'1 (Acil)' if failure_count > 5 else '2 (Önemli)' if failure_count > 2 else '3 (Normal)'}
- Tahmini Bütçe: {failure_count * 15}K - {failure_count * 25}K TL
- ROI: 6-12 ay içinde pozitif
"""}
            ]
        }
    
    def _create_comparison_qa(self, df):
        """Karşılaştırma soruları"""
        qa_pairs = []
        
        # Bölge karşılaştırması
        top_regions = df['bolge'].value_counts().head(2)
        if len(top_regions) >= 2:
            qa_pairs.append({
                "messages": [
                    {"role": "system", "content": "Bölgesel fiber performans analizi uzmanısın."},
                    {"role": "user", "content": f"{top_regions.index[0]} ve {top_regions.index[1]} bölgelerini karşılaştırır mısın?"},
                    {"role": "assistant", "content": f"""
📊 **Bölgesel Karşılaştırma Analizi**:

**{top_regions.index[0]} Bölgesi**:
- Arıza Sayısı: {top_regions.iloc[0]}
- Yoğunluk: {'Yüksek' if top_regions.iloc[0] > 5 else 'Orta'}
- Öncelik: 1

**{top_regions.index[1]} Bölgesi**:
- Arıza Sayısı: {top_regions.iloc[1]}
- Yoğunluk: {'Yüksek' if top_regions.iloc[1] > 5 else 'Orta'}
- Öncelik: 2

**Karşılaştırmalı Değerlendirme**:
- Fark: {abs(top_regions.iloc[0] - top_regions.iloc[1])} arıza
- Kritik Bölge: {top_regions.index[0]}
- Kaynak Dağılımı: %{int(top_regions.iloc[0]/(top_regions.iloc[0]+top_regions.iloc[1])*100)} - %{int(top_regions.iloc[1]/(top_regions.iloc[0]+top_regions.iloc[1])*100)}

**Öneriler**:
1. {top_regions.index[0]} bölgesine ekip takviyesi
2. Ortak sorunları tespit edip çözün
3. En iyi uygulamaları paylaşın
"""}
                ]
            })
        
        return qa_pairs
    
    def save_training_data(self, output_file: str = "ml_data/enhanced_training_data.jsonl"):
        """Training verisini kaydet"""
        # Mevcut veriyi yükle
        existing_data = []
        try:
            with open("ml_data/training_data.jsonl", 'r', encoding='utf-8') as f:
                for line in f:
                    existing_data.append(json.loads(line))
        except:
            pass
        
        # Yeni veri üret
        new_data = self.generate_qa_pairs(100)
        
        # Birleştir
        all_data = existing_data + new_data
        
        # Kaydet
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in all_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"✅ {len(all_data)} training örneği kaydedildi: {output_file}")
        print(f"   - Mevcut: {len(existing_data)}")
        print(f"   - Yeni: {len(new_data)}")
        
        # İstatistikler
        self._print_statistics(all_data)
    
    def _print_statistics(self, data):
        """Training verisi istatistikleri"""
        print("\n📊 Training Verisi İstatistikleri:")
        
        # Soru tipleri
        question_types = {
            "HAGS": 0,
            "Risk": 0,
            "Çözüm": 0,
            "Analiz": 0,
            "Genel": 0
        }
        
        for item in data:
            user_msg = item['messages'][1]['content'].lower()
            if 'hags' in user_msg:
                question_types['HAGS'] += 1
            elif 'risk' in user_msg or 'tahmin' in user_msg:
                question_types['Risk'] += 1
            elif 'çözüm' in user_msg or 'öneri' in user_msg:
                question_types['Çözüm'] += 1
            elif 'analiz' in user_msg or 'neden' in user_msg:
                question_types['Analiz'] += 1
            else:
                question_types['Genel'] += 1
        
        for qtype, count in question_types.items():
            print(f"   - {qtype}: {count} ({count/len(data)*100:.1f}%)")
        
        # Ortalama uzunluklar
        avg_q_len = sum(len(item['messages'][1]['content']) for item in data) / len(data)
        avg_a_len = sum(len(item['messages'][2]['content']) for item in data) / len(data)
        
        print(f"\n📏 Ortalama Uzunluklar:")
        print(f"   - Soru: {avg_q_len:.0f} karakter")
        print(f"   - Cevap: {avg_a_len:.0f} karakter")


if __name__ == "__main__":
    print("🚀 Training Data Genişletme")
    print("-" * 50)
    
    generator = TrainingDataGenerator()
    
    # Training verisi üret ve kaydet
    generator.save_training_data()
    
    print("\n💡 Sonraki Adımlar:")
    print("1. Fine-tuning için: ollama create fiber-expert -f ./Modelfile")
    print("2. Test için: python local_ai_setup.py")
    print("3. Daha fazla veri için: python generate_training_data.py")