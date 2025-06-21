#!/usr/bin/env python3
"""
KAREL Network Dashboard - AI Model Entegrasyonu
DeepSeek R1 veya benzeri modeller için entegrasyon modülü
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime, timedelta
import os

class FiberArizaAI:
    def __init__(self, model_type: str = "deepseek-r1", api_key: Optional[str] = None):
        """
        AI Model entegrasyon sınıfı
        
        Args:
            model_type: Kullanılacak model tipi (deepseek-r1, gpt-4, llama, vb.)
            api_key: API anahtarı (gerekiyorsa)
        """
        self.model_type = model_type
        self.api_key = api_key or os.getenv(f"{model_type.upper()}_API_KEY")
        self.ml_data_path = "ml_data"
        
    def load_data(self) -> Dict[str, pd.DataFrame]:
        """ML verilerini yükle"""
        data = {}
        
        # CSV dosyalarını yükle
        for file in os.listdir(self.ml_data_path):
            if file.endswith('.csv'):
                table_name = file.replace('.csv', '')
                data[table_name] = pd.read_csv(f"{self.ml_data_path}/{file}")
                
        # JSON analizini yükle
        with open(f"{self.ml_data_path}/database_analysis.json", 'r', encoding='utf-8') as f:
            data['analysis'] = json.load(f)
            
        return data
    
    def predict_future_failures(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Gelecekteki potansiyel arızaları tahmin et
        
        Args:
            days_ahead: Kaç gün sonrasını tahmin edeceğiz
            
        Returns:
            Tahmin edilen arıza listesi
        """
        data = self.load_data()
        df = data.get('fiber_ariza', pd.DataFrame())
        
        if len(df) == 0:
            return []
        
        predictions = []
        
        # Basit pattern analizi (gerçek ML modeli yerine)
        # TODO: Gerçek ML modeli entegre edilecek
        
        # Bölgesel arıza sıklığı analizi
        if 'bolge' in df.columns and 'ariza_baslangic' in df.columns:
            df['ariza_baslangic'] = pd.to_datetime(df['ariza_baslangic'], errors='coerce')
            
            # Son 30 günün arızaları
            recent_date = df['ariza_baslangic'].max() - timedelta(days=30)
            recent_failures = df[df['ariza_baslangic'] > recent_date]
            
            # Bölge bazlı risk skorları
            risk_scores = recent_failures.groupby('bolge').size().to_dict()
            
            for bolge, count in risk_scores.items():
                if count > 5:  # Yüksek risk threshold
                    predictions.append({
                        'prediction_type': 'high_risk_area',
                        'location': bolge,
                        'risk_score': min(count / 5, 1.0),  # 0-1 arası normalize
                        'predicted_failures': int(count * 0.3),  # %30 tahmin
                        'timeframe_days': days_ahead,
                        'confidence': 0.75,
                        'reasoning': f"Son 30 günde {count} arıza kaydı"
                    })
        
        # Kök neden bazlı tahmin
        if 'ariza_kok_neden' in df.columns:
            root_cause_freq = df['ariza_kok_neden'].value_counts().head(5)
            
            for cause, count in root_cause_freq.items():
                if pd.notna(cause) and count > 10:
                    predictions.append({
                        'prediction_type': 'recurring_issue',
                        'root_cause': cause,
                        'expected_occurrences': int(count * 0.1),
                        'timeframe_days': days_ahead,
                        'confidence': 0.65,
                        'prevention_suggestion': self._get_prevention_suggestion(cause)
                    })
        
        return predictions
    
    def _get_prevention_suggestion(self, root_cause: str) -> str:
        """Kök nedene göre önleme önerisi"""
        suggestions = {
            'kablo kopması': 'Kablo güzergahlarının düzenli kontrolü ve güçlendirme',
            'ek kutusu arızası': 'Ek kutularının periyodik bakımı ve yenilenmesi',
            'hafriyat': 'Hafriyat firmalarıyla koordinasyon ve uyarı sistemleri',
            'doğal afet': 'Kritik noktalara yedekli altyapı kurulumu',
            'ekipman arızası': 'Ekipman yaşlandırma takibi ve proaktif değişim'
        }
        
        for key, suggestion in suggestions.items():
            if key.lower() in root_cause.lower():
                return suggestion
        
        return "Detaylı analiz ve önleyici bakım planı önerilir"
    
    def analyze_with_llm(self, prompt: str) -> str:
        """
        LLM kullanarak analiz yap
        
        Args:
            prompt: Analiz için prompt
            
        Returns:
            Model yanıtı
        """
        if self.model_type == "deepseek-r1":
            return self._call_deepseek_r1(prompt)
        elif self.model_type == "gpt-4":
            return self._call_openai(prompt)
        else:
            return self._call_local_model(prompt)
    
    def _call_deepseek_r1(self, prompt: str) -> str:
        """DeepSeek R1 API çağrısı"""
        # TODO: Gerçek API entegrasyonu
        # Şimdilik simüle edilmiş yanıt
        return f"""
# Fiber Altyapı Analiz Raporu

## Mevcut Durum Analizi
Veritabanındaki {self._get_total_records()} kayıt üzerinden yapılan analizde:

### Kritik Bulgular:
1. **Yüksek Riskli Bölgeler**: Analiz sonucunda bazı bölgelerde arıza yoğunluğu tespit edildi
2. **HAGS Aşım Durumu**: Arızaların önemli bir kısmında HAGS süresi aşılmış
3. **Çözüm Oranı**: Mevcut çözüm oranı iyileştirmeye açık

### Öneriler:
1. **Proaktif Bakım**: Risk skorları yüksek bölgelerde önleyici bakım
2. **Kaynak Optimizasyonu**: Arıza yoğun bölgelere ekip takviyesi
3. **Altyapı Güçlendirme**: Sık arıza veren güzergahlarda kablo yenileme

## Tahminler:
Önümüzdeki 7 gün içinde yaklaşık 15-20 arıza beklenmektedir.
"""
    
    def _call_openai(self, prompt: str) -> str:
        """OpenAI API çağrısı"""
        # TODO: OpenAI API entegrasyonu
        pass
    
    def _call_local_model(self, prompt: str) -> str:
        """Yerel model çağrısı (Ollama, vb.)"""
        # TODO: Ollama veya benzeri local model entegrasyonu
        pass
    
    def _get_total_records(self) -> int:
        """Toplam kayıt sayısını al"""
        data = self.load_data()
        return len(data.get('fiber_ariza', pd.DataFrame()))
    
    def generate_dashboard_insights(self) -> Dict[str, Any]:
        """Dashboard için AI destekli içgörüler üret"""
        data = self.load_data()
        analysis = data.get('analysis', {})
        
        insights = {
            'generated_at': datetime.now().isoformat(),
            'summary': {},
            'alerts': [],
            'recommendations': [],
            'predictions': []
        }
        
        # Özet istatistikler
        if 'fiber_ariza' in analysis.get('table_analysis', {}):
            fa = analysis['table_analysis']['fiber_ariza']
            sa = fa.get('special_analysis', {})
            
            insights['summary'] = {
                'total_records': fa['row_count'],
                'hags_violation_rate': sa.get('hags_stats', {}).get('hags_percentage', 0),
                'solution_rate': sa.get('solution_stats', {}).get('solution_rate', 0),
                'coordinate_coverage': sa.get('coordinate_stats', {}).get('coordinate_coverage', 0)
            }
            
            # Uyarılar
            if insights['summary']['hags_violation_rate'] > 20:
                insights['alerts'].append({
                    'type': 'warning',
                    'message': f"HAGS aşım oranı %{insights['summary']['hags_violation_rate']:.1f} - Kritik seviyede!",
                    'priority': 'high'
                })
            
            if insights['summary']['solution_rate'] < 70:
                insights['alerts'].append({
                    'type': 'info',
                    'message': f"Çözüm oranı %{insights['summary']['solution_rate']:.1f} - İyileştirme gerekli",
                    'priority': 'medium'
                })
        
        # Tahminler
        insights['predictions'] = self.predict_future_failures(7)
        
        # Öneriler
        insights['recommendations'] = [
            {
                'title': 'Koordinat Verisi Tamamlama',
                'description': 'Koordinatsız arızaların lokasyon bilgileri tamamlanmalı',
                'impact': 'high',
                'effort': 'low'
            },
            {
                'title': 'HAGS Süre Optimizasyonu',
                'description': 'Yüksek HAGS aşım oranı için süreç iyileştirmesi',
                'impact': 'high',
                'effort': 'medium'
            }
        ]
        
        return insights
    
    def train_custom_model(self, model_path: str = "models/fiber_ariza_model.pkl"):
        """
        Özel ML modeli eğit
        
        Args:
            model_path: Modelin kaydedileceği yol
        """
        # TODO: Gerçek ML model eğitimi
        # - Random Forest, XGBoost, vb.
        # - Feature engineering
        # - Cross validation
        pass
    
    def export_training_data(self, output_file: str = "training_data.jsonl"):
        """
        Fine-tuning için JSONL formatında veri export et
        
        Args:
            output_file: Çıktı dosya adı
        """
        data = self.load_data()
        df = data.get('fiber_ariza', pd.DataFrame())
        
        training_examples = []
        
        for _, row in df.iterrows():
            # Her arıza kaydını soru-cevap formatına dönüştür
            example = {
                "messages": [
                    {
                        "role": "system",
                        "content": "Sen Türkiye fiber optik altyapı uzmanısın. Arıza analizi ve çözüm önerileri sunuyorsun."
                    },
                    {
                        "role": "user",
                        "content": f"Bölge: {row.get('bolge', 'Bilinmiyor')}, "
                                 f"İl: {row.get('il', 'Bilinmiyor')}, "
                                 f"Arıza nedeni: {row.get('ariza_kok_neden', 'Bilinmiyor')}. "
                                 f"Bu arıza için analiz ve öneri?"
                    },
                    {
                        "role": "assistant",
                        "content": f"Arıza Analizi:\n"
                                 f"- Lokasyon: {row.get('lokasyon', 'Belirtilmemiş')}\n"
                                 f"- HAGS Durumu: {row.get('hags_asildi_mi', 'Bilinmiyor')}\n"
                                 f"- Çözüm Durumu: {row.get('kalici_cozum', 'Devam ediyor')}\n"
                                 f"- Süre: {row.get('ariza_suresi', 'Hesaplanıyor')}\n\n"
                                 f"Öneriler:\n"
                                 f"1. {self._get_prevention_suggestion(row.get('ariza_kok_neden', ''))}\n"
                                 f"2. Benzer arızaları önlemek için periyodik kontrol\n"
                                 f"3. {'Koordinat bilgisi eklenmeli' if pd.isna(row.get('kordinat_a')) else 'Lokasyon takibi aktif'}"
                    }
                ]
            }
            training_examples.append(example)
        
        # JSONL formatında kaydet
        with open(f"{self.ml_data_path}/{output_file}", 'w', encoding='utf-8') as f:
            for example in training_examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        print(f"✅ {len(training_examples)} training örneği {output_file} dosyasına kaydedildi")


# CLI kullanımı
if __name__ == "__main__":
    print("🤖 KAREL Network Dashboard - AI Entegrasyonu")
    print("-" * 50)
    
    # AI modülü oluştur
    ai = FiberArizaAI(model_type="deepseek-r1")
    
    # Dashboard insights üret
    print("\n📊 Dashboard İçgörüleri Üretiliyor...")
    insights = ai.generate_dashboard_insights()
    
    print(f"\n📈 Özet:")
    print(f"  - Toplam Kayıt: {insights['summary'].get('total_records', 0)}")
    print(f"  - HAGS Aşım Oranı: %{insights['summary'].get('hags_violation_rate', 0):.1f}")
    print(f"  - Çözüm Oranı: %{insights['summary'].get('solution_rate', 0):.1f}")
    
    # Tahminler
    print(f"\n🔮 Tahminler ({len(insights['predictions'])} adet):")
    for pred in insights['predictions'][:3]:
        print(f"  - {pred['prediction_type']}: {pred.get('location', pred.get('root_cause', 'N/A'))}")
        print(f"    Risk: %{pred.get('risk_score', pred.get('confidence', 0))*100:.0f}")
    
    # Uyarılar
    if insights['alerts']:
        print(f"\n⚠️  Uyarılar:")
        for alert in insights['alerts']:
            print(f"  - [{alert['priority'].upper()}] {alert['message']}")
    
    # Training data export
    print("\n📝 Fine-tuning Verisi Hazırlanıyor...")
    ai.export_training_data()
    
    # Sonuçları kaydet
    with open('ml_data/ai_insights.json', 'w', encoding='utf-8') as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)
    print("\n✅ AI içgörüleri ai_insights.json dosyasına kaydedildi")