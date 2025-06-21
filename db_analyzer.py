#!/usr/bin/env python3
"""
KAREL Network Dashboard - AI/ML Veri Hazırlama Modülü
Bu script SQLite veritabanını okur ve AI modellerinin anlayabileceği formatlara dönüştürür.
"""

import sqlite3
import pandas as pd
import json
import numpy as np
from datetime import datetime
import os
from typing import Dict, List, Any

class FiberArizaAnalyzer:
    def __init__(self, db_path: str = 'instance/fiberariza.db'):
        """
        Veritabanı analiz sınıfı
        
        Args:
            db_path: SQLite veritabanı dosya yolu
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.tables = self._get_tables()
        
    def _get_tables(self) -> List[str]:
        """Veritabanındaki tüm tabloları listele"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [table[0] for table in cursor.fetchall() if not table[0].startswith('sqlite_')]
    
    def analyze_database(self) -> Dict[str, Any]:
        """Veritabanı genel analizi"""
        analysis = {
            'database_info': {
                'path': self.db_path,
                'size_mb': os.path.getsize(self.db_path) / (1024 * 1024),
                'tables': self.tables,
                'analysis_date': datetime.now().isoformat()
            },
            'table_analysis': {}
        }
        
        for table in self.tables:
            analysis['table_analysis'][table] = self._analyze_table(table)
        
        return analysis
    
    def _analyze_table(self, table_name: str) -> Dict[str, Any]:
        """Tek bir tabloyu analiz et"""
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", self.conn)
        
        analysis = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'data_types': df.dtypes.astype(str).to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'unique_counts': {col: df[col].nunique() for col in df.columns},
            'sample_data': df.head(5).to_dict(orient='records')
        }
        
        # Özel analizler
        if table_name == 'fiber_ariza':
            analysis['special_analysis'] = self._analyze_fiber_ariza(df)
        
        return analysis
    
    def _analyze_fiber_ariza(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Fiber arıza tablosu için özel analizler"""
        analysis = {}
        
        # Bölgesel dağılım
        if 'bolge' in df.columns:
            analysis['bolge_distribution'] = df['bolge'].value_counts().to_dict()
        
        # HAGS analizi
        if 'hags_asildi_mi' in df.columns:
            analysis['hags_stats'] = {
                'total': len(df),
                'hags_exceeded': len(df[df['hags_asildi_mi'] == 'Evet']),
                'hags_percentage': (len(df[df['hags_asildi_mi'] == 'Evet']) / len(df) * 100) if len(df) > 0 else 0
            }
        
        # Kalıcı çözüm analizi
        if 'kalici_cozum' in df.columns:
            analysis['solution_stats'] = {
                'solved': len(df[df['kalici_cozum'] == 'Evet']),
                'unsolved': len(df[df['kalici_cozum'] != 'Evet']),
                'solution_rate': (len(df[df['kalici_cozum'] == 'Evet']) / len(df) * 100) if len(df) > 0 else 0
            }
        
        # Koordinatlı arıza analizi
        if 'kordinat_a' in df.columns and 'kordinat_b' in df.columns:
            coords_filled = df[(df['kordinat_a'].notna()) & (df['kordinat_b'].notna())]
            analysis['coordinate_stats'] = {
                'with_coordinates': len(coords_filled),
                'without_coordinates': len(df) - len(coords_filled),
                'coordinate_coverage': (len(coords_filled) / len(df) * 100) if len(df) > 0 else 0
            }
        
        # Arıza süreleri analizi
        if 'ariza_baslangic' in df.columns and 'ariza_bitis' in df.columns:
            df['ariza_baslangic'] = pd.to_datetime(df['ariza_baslangic'], errors='coerce')
            df['ariza_bitis'] = pd.to_datetime(df['ariza_bitis'], errors='coerce')
            
            valid_dates = df[(df['ariza_baslangic'].notna()) & (df['ariza_bitis'].notna())]
            if len(valid_dates) > 0:
                valid_dates['duration_hours'] = (valid_dates['ariza_bitis'] - valid_dates['ariza_baslangic']).dt.total_seconds() / 3600
                analysis['duration_stats'] = {
                    'avg_duration_hours': valid_dates['duration_hours'].mean(),
                    'max_duration_hours': valid_dates['duration_hours'].max(),
                    'min_duration_hours': valid_dates['duration_hours'].min(),
                    'median_duration_hours': valid_dates['duration_hours'].median()
                }
        
        # Kök neden analizi
        if 'ariza_kok_neden' in df.columns:
            analysis['root_cause_distribution'] = df['ariza_kok_neden'].value_counts().head(10).to_dict()
        
        return analysis
    
    def export_for_ml(self, output_dir: str = 'ml_data') -> None:
        """ML modelleri için veriyi export et"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Her tablo için CSV export
        for table in self.tables:
            df = pd.read_sql_query(f"SELECT * FROM {table}", self.conn)
            df.to_csv(f"{output_dir}/{table}.csv", index=False)
            print(f"✅ {table}.csv exported ({len(df)} rows)")
        
        # Analiz sonuçlarını JSON olarak kaydet
        analysis = self.analyze_database()
        with open(f"{output_dir}/database_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print("✅ database_analysis.json exported")
        
        # ML için özel hazırlanmış veri
        self._prepare_ml_dataset(output_dir)
    
    def _prepare_ml_dataset(self, output_dir: str) -> None:
        """ML modelleri için özel veri hazırla"""
        # Fiber arıza verisi için feature engineering
        df = pd.read_sql_query("SELECT * FROM fiber_ariza", self.conn)
        
        if len(df) > 0:
            # Feature engineering
            features = pd.DataFrame()
            
            # Kategorik değişkenleri encode et
            if 'bolge' in df.columns:
                features['bolge_encoded'] = pd.Categorical(df['bolge']).codes
            
            if 'hags_asildi_mi' in df.columns:
                features['hags_exceeded'] = (df['hags_asildi_mi'] == 'Evet').astype(int)
            
            if 'kalici_cozum' in df.columns:
                features['is_solved'] = (df['kalici_cozum'] == 'Evet').astype(int)
            
            # Koordinat features
            if 'kordinat_a' in df.columns and 'kordinat_b' in df.columns:
                features['has_coordinates'] = ((df['kordinat_a'].notna()) & (df['kordinat_b'].notna())).astype(int)
                
                # Koordinatları float'a çevir
                df['kordinat_a'] = pd.to_numeric(df['kordinat_a'].astype(str).str.replace(',', '.'), errors='coerce')
                df['kordinat_b'] = pd.to_numeric(df['kordinat_b'].astype(str).str.replace(',', '.'), errors='coerce')
                
                features['latitude'] = df['kordinat_a'].fillna(0)
                features['longitude'] = df['kordinat_b'].fillna(0)
            
            # Zaman features
            if 'ariza_baslangic' in df.columns:
                df['ariza_baslangic'] = pd.to_datetime(df['ariza_baslangic'], errors='coerce')
                features['start_hour'] = df['ariza_baslangic'].dt.hour
                features['start_day_of_week'] = df['ariza_baslangic'].dt.dayofweek
                features['start_month'] = df['ariza_baslangic'].dt.month
            
            # ML-ready dataset
            ml_dataset = pd.concat([features, df[['bulten_no', 'il', 'ariza_kok_neden']]], axis=1)
            ml_dataset.to_csv(f"{output_dir}/ml_ready_dataset.csv", index=False)
            print("✅ ml_ready_dataset.csv exported")
            
            # Text data for NLP
            text_data = []
            for _, row in df.iterrows():
                text_entry = {
                    'bulten_no': row.get('bulten_no', ''),
                    'description': f"{row.get('guzergah', '')} {row.get('lokasyon', '')} {row.get('aciklama', '')}",
                    'root_cause': row.get('ariza_kok_neden', ''),
                    'consolidated_cause': row.get('ariza_konsolide', ''),
                    'is_solved': row.get('kalici_cozum', '') == 'Evet'
                }
                text_data.append(text_entry)
            
            with open(f"{output_dir}/text_data_for_nlp.json", 'w', encoding='utf-8') as f:
                json.dump(text_data, f, ensure_ascii=False, indent=2)
            print("✅ text_data_for_nlp.json exported")
    
    def generate_insights_prompt(self) -> str:
        """R1 modeli için prompt oluştur"""
        analysis = self.analyze_database()
        
        prompt = f"""
# Fiber Optik Arıza Veritabanı Analizi

## Veritabanı Özeti:
- Toplam tablo sayısı: {len(self.tables)}
- Veritabanı boyutu: {analysis['database_info']['size_mb']:.2f} MB

## Fiber Arıza Tablosu Detayları:
"""
        
        if 'fiber_ariza' in analysis['table_analysis']:
            fa = analysis['table_analysis']['fiber_ariza']
            prompt += f"""
- Toplam arıza kaydı: {fa['row_count']}
- Sütun sayısı: {fa['column_count']}
"""
            
            if 'special_analysis' in fa:
                sa = fa['special_analysis']
                
                if 'hags_stats' in sa:
                    prompt += f"""
### HAGS Analizi:
- HAGS aşan arıza sayısı: {sa['hags_stats']['hags_exceeded']} ({sa['hags_stats']['hags_percentage']:.1f}%)
"""
                
                if 'solution_stats' in sa:
                    prompt += f"""
### Çözüm Durumu:
- Çözülen arızalar: {sa['solution_stats']['solved']} ({sa['solution_stats']['solution_rate']:.1f}%)
- Çözülmeyen arızalar: {sa['solution_stats']['unsolved']}
"""
                
                if 'coordinate_stats' in sa:
                    prompt += f"""
### Koordinat Kapsama:
- Koordinatlı arızalar: {sa['coordinate_stats']['with_coordinates']} ({sa['coordinate_stats']['coordinate_coverage']:.1f}%)
"""
                
                if 'duration_stats' in sa:
                    prompt += f"""
### Arıza Süre İstatistikleri:
- Ortalama arıza süresi: {sa['duration_stats']['avg_duration_hours']:.1f} saat
- En uzun arıza: {sa['duration_stats']['max_duration_hours']:.1f} saat
- En kısa arıza: {sa['duration_stats']['min_duration_hours']:.1f} saat
"""
                
                if 'root_cause_distribution' in sa:
                    prompt += "\n### En Sık Arıza Nedenleri:\n"
                    for cause, count in list(sa['root_cause_distribution'].items())[:5]:
                        prompt += f"- {cause}: {count} kez\n"
        
        prompt += """
## Analiz Soruları:
1. Bu verilere göre en kritik arıza bölgeleri hangileri?
2. HAGS aşım oranını azaltmak için hangi önlemler alınabilir?
3. Çözülmeyen arızaların ortak özellikleri neler?
4. Arıza sürelerini kısaltmak için ne önerirsiniz?
5. Gelecekteki potansiyel arıza bölgeleri tahmin edilebilir mi?

Lütfen bu verileri analiz ederek Türkiye fiber altyapısı için öneriler sunun.
"""
        
        return prompt
    
    def close(self):
        """Veritabanı bağlantısını kapat"""
        self.conn.close()


# CLI kullanımı
if __name__ == "__main__":
    print("🔍 KAREL Network Dashboard - AI/ML Veri Hazırlama")
    print("-" * 50)
    
    # Analyzer oluştur
    analyzer = FiberArizaAnalyzer()
    
    # Veritabanı analizi
    print("\n📊 Veritabanı Analizi Başlıyor...")
    analysis = analyzer.analyze_database()
    
    print(f"\n✅ Toplam {len(analyzer.tables)} tablo bulundu:")
    for table in analyzer.tables:
        row_count = analysis['table_analysis'][table]['row_count']
        print(f"  - {table}: {row_count} kayıt")
    
    # ML export
    print("\n📁 ML Verileri Export Ediliyor...")
    analyzer.export_for_ml()
    
    # R1 prompt oluştur
    print("\n🤖 R1 Modeli İçin Prompt Oluşturuluyor...")
    prompt = analyzer.generate_insights_prompt()
    
    with open('ml_data/r1_analysis_prompt.txt', 'w', encoding='utf-8') as f:
        f.write(prompt)
    print("✅ r1_analysis_prompt.txt kaydedildi")
    
    # Özet istatistikler
    if 'fiber_ariza' in analysis['table_analysis']:
        fa = analysis['table_analysis']['fiber_ariza']['special_analysis']
        print("\n📈 Özet İstatistikler:")
        print(f"  - HAGS Aşım Oranı: {fa.get('hags_stats', {}).get('hags_percentage', 0):.1f}%")
        print(f"  - Çözüm Oranı: {fa.get('solution_stats', {}).get('solution_rate', 0):.1f}%")
        print(f"  - Koordinat Kapsama: {fa.get('coordinate_stats', {}).get('coordinate_coverage', 0):.1f}%")
    
    analyzer.close()
    print("\n✅ Analiz tamamlandı! ml_data/ klasörünü kontrol edin.")