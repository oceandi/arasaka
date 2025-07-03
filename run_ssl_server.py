"""
SSL Server Runner for Windows
Runs Flask app with HTTPS using Python's built-in SSL
"""
import ssl
import os
from app import app

# SSL certificate paths
SSL_CERT = os.environ.get('SSL_CERT', r'C:\ssl\maintencesp.com.tr\fullchain.pem')
SSL_KEY = os.environ.get('SSL_KEY', r'C:\ssl\maintencesp.com.tr\privkey.pem')

# Verify files exist
if not os.path.exists(SSL_CERT):
    print(f"❌ SSL certificate not found: {SSL_CERT}")
    exit(1)
    
if not os.path.exists(SSL_KEY):
    print(f"❌ SSL private key not found: {SSL_KEY}")
    exit(1)

print("✅ SSL files found")
print(f"📜 Certificate: {SSL_CERT}")
print(f"🔑 Private Key: {SSL_KEY}")

# Create SSL context
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(SSL_CERT, SSL_KEY)

# Run the application
if __name__ == '__main__':
    print("\n🚀 Starting HTTPS server...")
    print("🌐 Access at: https://maintencesp.com.tr")
    print("🔒 SSL/TLS enabled")
    print("⚠️  Press CTRL+C to stop\n")
    
    try:
        app.run(
            host='0.0.0.0',
            port=443,
            ssl_context=context,
            debug=False
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPossible solutions:")
        print("1. Make sure port 443 is not in use")
        print("2. Run as Administrator")
        print("3. Check firewall settings")