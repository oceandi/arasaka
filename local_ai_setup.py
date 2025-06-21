#!/usr/bin/env python3
"""
KAREL Network Dashboard - Local AI Setup
Ollama ve diğer local model seçenekleri
"""

import subprocess
import requests
import json
import os
from typing import Dict, Any, Optional
import platform

class LocalAISetup:
    def __init__(self):
        self.os_type = platform.system()
        self.ollama_url = "http://localhost:11434"
        
    def check_ollama_installed(self) -> bool:
        """Ollama'nın kurulu olup olmadığını kontrol et"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    def install_ollama(self):
        """Ollama kurulum talimatları"""
        print("🤖 Ollama Kurulumu")
        print("-" * 50)
        
        if self.os_type == "Windows":
            print("""
Windows için Ollama kurulumu:

1. Tarayıcıdan indirin:
   https://ollama.ai/download/windows
   
2. OllamaSetup.exe dosyasını çalıştırın

3. Kurulum tamamlandıktan sonra PowerShell'de:
   ollama --version
   
4. Ollama'yı başlatın:
   ollama serve
""")
        elif self.os_type == "Linux":
            print("""
Linux için Ollama kurulumu:

curl -fsSL https://ollama.ai/install.sh | sh
""")
        elif self.os_type == "Darwin":  # macOS
            print("""
macOS için Ollama kurulumu:

brew install ollama
""")
    
    def download_models(self):
        """Önerilen modelleri indir"""
        models = [
            {
                "name": "deepseek-r1:1.5b",
                "size": "1GB",
                "description": "DeepSeek R1 1.5B - Hızlı ve hafif"
            },
            {
                "name": "deepseek-r1:7b",
                "size": "4GB",
                "description": "DeepSeek R1 7B - Dengeli performans"
            },
            {
                "name": "llama3.2:3b",
                "size": "2GB",
                "description": "Llama 3.2 3B - Alternatif model"
            },
            {
                "name": "qwen2.5:3b",
                "size": "2GB",
                "description": "Qwen 2.5 3B - Türkçe desteği iyi"
            }
        ]
        
        print("\n📦 İndirilebilecek Modeller:")
        for i, model in enumerate(models, 1):
            print(f"\n{i}. {model['name']}")
            print(f"   Boyut: {model['size']}")
            print(f"   Açıklama: {model['description']}")
            print(f"   İndirme komutu: ollama pull {model['name']}")
    
    def test_model(self, model_name: str = "deepseek-r1:1.5b"):
        """Model testi"""
        print(f"\n🧪 {model_name} Model Testi")
        print("-" * 50)
        
        test_prompt = """
        Fiber optik arıza veritabanı analizi:
        - Toplam 3 arıza kaydı
        - HAGS aşım oranı: %33.3
        - Çözüm oranı: %66.7
        
        Bu verilere göre önerileriniz nelerdir?
        """
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": test_prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Model Yanıtı:")
                print(result.get("response", "Yanıt alınamadı"))
            else:
                print(f"❌ Hata: {response.status_code}")
                print("Model indirilmemiş olabilir. Önce: ollama pull", model_name)
        except Exception as e:
            print(f"❌ Bağlantı hatası: {str(e)}")
            print("Ollama servisinin çalıştığından emin olun: ollama serve")


class FiberArizaLocalAI:
    """Fiber arıza analizi için local AI"""
    
    def __init__(self, model_name: str = "deepseek-r1:7b"):  # 7b varsayılan
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434"
        self.context_loaded = False
        self.context = ""
        
    def load_context(self):
        """Veritabanı bağlamını yükle"""
        try:
            # Analiz sonuçlarını yükle
            with open('ml_data/database_analysis.json', 'r', encoding='utf-8') as f:
                analysis = json.load(f)
            
            # Training verilerini yükle (ilk 10 örnek)
            training_examples = []
            with open('ml_data/training_data.jsonl', 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= 10:  # Sadece ilk 10 örnek
                        break
                    training_examples.append(json.loads(line))
            
            # Context oluştur
            self.context = f"""
Sen Türkiye fiber optik altyapı uzmanısın. KAREL Network Dashboard veritabanını analiz ediyorsun.

## Veritabanı Özeti:
- Toplam fiber arıza kaydı: {analysis['table_analysis']['fiber_ariza']['row_count']}
- HAGS aşım oranı: %{analysis['table_analysis']['fiber_ariza']['special_analysis']['hags_stats']['hags_percentage']:.1f}
- Çözüm oranı: %{analysis['table_analysis']['fiber_ariza']['special_analysis']['solution_stats']['solution_rate']:.1f}
- Koordinat kapsama: %{analysis['table_analysis']['fiber_ariza']['special_analysis']['coordinate_stats']['coordinate_coverage']:.1f}

## En Sık Arıza Nedenleri:
"""
            root_causes = analysis['table_analysis']['fiber_ariza']['special_analysis'].get('root_cause_distribution', {})
            for cause, count in list(root_causes.items())[:5]:
                self.context += f"- {cause}: {count} kez\n"
            
            self.context += "\n## Örnek Arıza Kayıtları:\n"
            for example in training_examples[:3]:
                user_msg = example['messages'][1]['content']
                self.context += f"- {user_msg}\n"
            
            self.context_loaded = True
            print("✅ Context yüklendi")
            
        except Exception as e:
            print(f"❌ Context yükleme hatası: {str(e)}")
            self.context = "Fiber optik arıza takip sistemi uzmanısın."
    
    def analyze(self, prompt: str, temperature: float = 0.7) -> str:
        """Analiz yap"""
        if not self.context_loaded:
            self.load_context()
        
        full_prompt = f"{self.context}\n\nKullanıcı Sorusu: {prompt}\n\nYanıt:"
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "temperature": temperature,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return response.json().get("response", "Yanıt alınamadı")
            else:
                return f"Hata: {response.status_code}"
        except Exception as e:
            return f"Bağlantı hatası: {str(e)}"
    
    def chat_interactive(self):
        """İnteraktif sohbet modu"""
        print(f"\n💬 {self.model_name} ile Fiber Arıza Analizi")
        print("(Çıkmak için 'exit' yazın)")
        print("-" * 50)
        
        self.load_context()
        
        while True:
            user_input = input("\n👤 Soru: ")
            
            if user_input.lower() in ['exit', 'quit', 'çıkış']:
                print("👋 Görüşmek üzere!")
                break
            
            print("\n🤖 Analiz ediliyor...")
            response = self.analyze(user_input)
            print(f"\n💡 Yanıt:\n{response}")
    
    def generate_report(self) -> str:
        """Otomatik rapor üret"""
        report_prompt = """
        Lütfen aşağıdaki başlıklarda detaylı bir analiz raporu hazırla:
        
        1. Mevcut Durum Özeti
        2. Kritik Bulgular
        3. Risk Analizi
        4. Çözüm Önerileri
        5. Öncelikli Aksiyon Planı
        
        Raporu Türkçe hazırla ve somut öneriler sun.
        """
        
        return self.analyze(report_prompt, temperature=0.3)  # Daha tutarlı çıktı için düşük temperature


# Örnek kullanım scripti
def main():
    print("🚀 KAREL Network Dashboard - Local AI Kurulumu")
    print("=" * 50)
    
    # Setup kontrolü
    setup = LocalAISetup()
    
    if not setup.check_ollama_installed():
        print("⚠️  Ollama kurulu değil!")
        setup.install_ollama()
        return
    
    print("✅ Ollama kurulu ve çalışıyor!")
    
    # Model seçenekleri
    setup.download_models()
    
    # Kullanıcı seçimi
    print("\n" + "=" * 50)
    choice = input("\nNe yapmak istersiniz?\n1. Model indir\n2. Model test et\n3. İnteraktif analiz\n4. Otomatik rapor\n\nSeçim (1-4): ")
    
    if choice == "1":
        model = input("\nModel adı (örn: deepseek-r1:1.5b): ")
        print(f"\nİndirmek için: ollama pull {model}")
        
    elif choice == "2":
        model = "deepseek-r1:7b"  # Otomatik 7b
        setup.test_model(model)
        
    elif choice == "3":
        model = "deepseek-r1:7b"  # Otomatik 7b
        ai = FiberArizaLocalAI(model)
        ai.chat_interactive()
        
    elif choice == "4":
        model = "deepseek-r1:7b"  # Otomatik 7b
        ai = FiberArizaLocalAI(model)
        print("\n📊 Rapor hazırlanıyor...")
        report = ai.generate_report()
        print(f"\n📄 RAPOR:\n{report}")
        
        # Raporu kaydet
        with open('ml_data/ai_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print("\n✅ Rapor 'ml_data/ai_report.txt' dosyasına kaydedildi")


if __name__ == "__main__":
    main()