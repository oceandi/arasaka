"""
Optimized SSL Server Runner - Takılma sorununu çözer
"""
import ssl
import os
import logging
from app import app
from datetime import datetime

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SSL dosyaları
SSL_CERT = r'C:\ssl\maintencesp.com.tr\fullchain.pem'
SSL_KEY = r'C:\ssl\maintencesp.com.tr\privkey.pem'

# SSL context - Daha modern protokol
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(SSL_CERT, SSL_KEY)

# Flask optimizasyonları
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 yıl cache
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

if __name__ == '__main__':
    logger.info("🚀 HTTPS Server başlatılıyor...")
    logger.info(f"🌐 Domain: https://maintencesp.com.tr")
    logger.info(f"🔒 SSL/TLS aktif")
    logger.info(f"📅 Başlangıç: {datetime.now()}")
    
    try:
        # Threaded=True takılmaları azaltır
        app.run(
            host='0.0.0.0',
            port=443,
            ssl_context=context,
            debug=False,
            threaded=True,  # Multi-thread desteği
            use_reloader=False  # Reloader kapalı (daha stabil)
        )
    except KeyboardInterrupt:
        logger.info("\n⏹️ Server kapatıldı")
    except Exception as e:
        logger.error(f"❌ Hata: {e}")
        logger.info("🔄 Server'ı yeniden başlatın")