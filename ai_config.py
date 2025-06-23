"""
KAREL Network Dashboard - AI Konfigürasyon
"""

# AI Model Ayarları
AI_CONFIG = {
    "model": "qwen2.5:3b",  # Varsayılan model
    "ollama_url": "http://localhost:11434",
    "temperature": 0.7,
    "timeout": 60,
    "max_tokens": 2000
}

# Flask app.py'ye eklenecek import
# from ai_config import AI_CONFIG

# Basit test fonksiyonu
def test_ai_connection():
    """AI bağlantısını test et"""
    import requests
    try:
        response = requests.get(f"{AI_CONFIG['ollama_url']}/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("✅ Ollama bağlantısı başarılı!")
            print(f"📦 Yüklü modeller: {[m['name'] for m in models]}")
            return True
        else:
            print("❌ Ollama bağlantısı başarısız!")
            return False
    except:
        print("❌ Ollama servisi çalışmıyor! 'ollama serve' komutunu çalıştırın.")
        return False

if __name__ == "__main__":
    test_ai_connection()