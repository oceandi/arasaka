# 🌐 M.S.P - Maintenance Solution Partner

## 🏢 Enterprise Fiber Optik Yönetim Sistemi

**M.S.P (Maintenance Solution Partner)**, Turkcell-Karel-Bayi ekosistemi için geliştirilmiş, enterprise seviyesinde fiber optik altyapı yönetim platformudur. Güvenli authentication, role-based access control ve comprehensive logging ile production-ready çözüm sunar.

## 🚀 **HTTPS Production Deployment**

### **Domain:** `https://maintence.com.tr`
### **IP:** `85.105.220.36`

### 🔐 **Windows SSL Kurulumu (Otomatik)**

```batch
REM 1. Ana kurulum (Administrator olarak çalıştır)
windows_ssl_setup.bat

REM 2. SSL sertifikası için Win-ACME kurulumu
install_winacme.bat

REM 3. HTTPS production başlatma
start_https.bat

REM 4. Test amaçlı HTTP başlatma
start_dev.bat
```

### 📋 **DNS Ayarları**
```
A Record: maintence.com.tr → 85.105.220.36
A Record: www.maintence.com.tr → 85.105.220.36
```

### 🖥️ **Windows Server Kurulum Adımları**

1. **Administrator olarak PowerShell/CMD açın**
2. **Proje klasörüne gidin**
3. **`windows_ssl_setup.bat` çalıştırın**
4. **SSL seçeneklerinden birini seçin:**
   - Option 1: Win-ACME (Let's Encrypt) - Önerilen
   - Option 2: Mevcut sertifika
   - Option 3: HTTP mode (test için)

### 🚀 **Production Başlatma**
```batch
REM HTTPS (SSL ile)
start_https.bat

REM HTTP (test için)  
start_dev.bat
```

## 🔐 **Enterprise Authentication System**

### **User Roles & Permissions**
- **Super Admin** - Sistem yöneticisi (tüm yetkiler)
- **Admin** - Bölge yöneticisi (kendi bölgesi)
- **Karel User** - Altyapı firması personeli (teknik işlemler)
- **Bayi User** - Bölge bayisi (sınırlı erişim)

### **Default Users**
| Username | Password | Role | Access |
|----------|----------|------|--------|
| `admin` | `Karel2024!` | Super Admin | All |
| `onur` | `Onur2024!` | Super Admin | All |
| `karel_bursa` | `Karel2024!` | Karel User | Bursa |
| `admin_bursa` | `Admin2024!` | Admin | Bursa |

### **Security Features**
- ✅ **Password Hashing** - Werkzeug Security
- ✅ **Session Management** - Flask-Login
- ✅ **Role-based Access Control** - Decorator-based protection
- ✅ **Region-based Data Filtering** - Geographical restrictions
- ✅ **Audit Logging** - All user actions logged
- ✅ **Enterprise UI/UX** - Professional interface

## 🛡️ **Production Security**

### **SSL/HTTPS Configuration**
```python
# Production SSL setup (built-in)
if is_production:
    ssl_context = (cert_path, key_path)
    app.run(host='0.0.0.0', port=443, ssl_context=ssl_context)
```

### **Logging & Monitoring**
- **Structured JSON Logs** - Machine-readable format
- **Audit Trail** - User actions, API calls, database operations
- **Error Tracking** - Comprehensive error logging
- **Performance Monitoring** - Request/response timing

### **Database Security**
- **Input Validation** - SQLAlchemy ORM protection
- **SQL Injection Prevention** - Parameterized queries
- **Data Encryption** - Password hashing
- **Access Control** - User-specific data filtering

## 🏗️ **System Architecture**

### **Tech Stack**
- **Backend**: Flask (Python 3.12+)
- **Database**: SQLite + SQLAlchemy ORM
- **Authentication**: Flask-Login + Werkzeug Security
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Production Server**: Gunicorn WSGI
- **SSL/TLS**: Let's Encrypt
- **Logging**: Python logging + JSON formatting

### **Core Modules**
1. **Fiber Arıza Takibi** - Main fault tracking system
2. **User Management** - Admin panel for user operations
3. **Region Management** - Geographical data organization
4. **Audit & Logging** - Security monitoring
5. **File Operations** - Excel import/export, KMZ generation

## 📦 **Quick Start**

### **Development Mode**
```bash
# 1. Clone & Setup
git clone [repository]
cd arasaka

# 2. Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Initialize Database
python init_users.py

# 5. Run Development Server
python app.py

# 6. Access
http://127.0.0.1:5001
```

### **Production Mode**
```bash
# 1. Environment Setup
export FLASK_ENV=production
export SSL_CERT_PATH="/etc/letsencrypt/live/maintencesp.com/fullchain.pem"
export SSL_KEY_PATH="/etc/letsencrypt/live/maintencesp.com/privkey.pem"

# 2. Run Production
sudo ./run_production.sh

# 3. Access
https://maintencesp.com
```

## 🎯 **Feature Highlights**

### **Admin Panel Features**
- **User Management** - Create, edit, delete users
- **Role Assignment** - Dynamic permission management
- **Region Management** - Geographical access control
- **System Statistics** - Real-time dashboard
- **Audit Logs** - Security monitoring

### **Authentication Features**
- **Secure Login** - Professional enterprise UI
- **Session Management** - Automatic logout, remember me
- **Password Security** - Strength validation, secure hashing
- **Access Control** - Route-level permission enforcement
- **Multi-region Support** - Scalable geographical organization

### **Production Features**
- **HTTPS/SSL** - Let's Encrypt integration
- **Load Balancing** - Gunicorn multi-worker support
- **Performance Monitoring** - Request timing and logging
- **Error Handling** - Comprehensive error management
- **Backup & Recovery** - Database migration support

## 🔧 **API Endpoints**

### **Authentication API**
- `POST /login` - User authentication
- `GET /logout` - Session termination
- `GET /admin` - Admin panel (auth required)

### **User Management API**
- `GET /admin/users` - List all users
- `POST /admin/user/create` - Create new user
- `PUT /admin/user/<id>/edit` - Edit user
- `DELETE /admin/user/<id>/delete` - Delete user

### **Core Business API**
- `GET /api/arizalar` - Fault data (region-filtered)
- `POST /api/ariza` - Create fault record
- `PUT /api/ariza/<id>` - Update fault record
- `DELETE /api/ariza/<id>` - Delete fault record

## 🏢 **Enterprise Deployment**

### **System Requirements**
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.12+
- **Memory**: 2GB+ RAM
- **Storage**: 10GB+ SSD
- **Network**: Public IP, Domain DNS

### **Production Checklist**
- ✅ SSL Certificate (Let's Encrypt)
- ✅ Firewall Configuration (ports 80, 443)
- ✅ DNS Records (A records)
- ✅ Environment Variables
- ✅ Database Backup Strategy
- ✅ Log Rotation Configuration
- ✅ Monitoring Setup

### **Scalability**
- **Multi-region Ready** - Easy geographical expansion
- **Load Balancer Compatible** - Gunicorn multi-worker
- **Database Scalable** - SQLite → PostgreSQL migration ready
- **CDN Compatible** - Static assets optimized

## 🛠️ **Configuration**

### **Environment Variables**
```bash
# Production Environment
FLASK_ENV=production
FLASK_APP=app.py
SSL_CERT_PATH=/etc/letsencrypt/live/maintencesp.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/maintencesp.com/privkey.pem
SECRET_KEY=your-super-secret-key
PORT=443
HOST=0.0.0.0
```

### **Gunicorn Configuration**
```bash
# Production WSGI Server
gunicorn --bind 0.0.0.0:443 \
         --workers 4 \
         --worker-class sync \
         --timeout 30 \
         --certfile=$SSL_CERT_PATH \
         --keyfile=$SSL_KEY_PATH \
         app:app
```

## 📊 **Monitoring & Analytics**

### **Log Files**
- `logs/app.log` - Application logs (JSON format)
- `logs/error.log` - Error logs only
- `logs/access.log` - HTTP access logs
- `logs/audit.log` - User action audit trail

### **Dashboard Metrics**
- **User Activity** - Login/logout tracking
- **System Performance** - Response times
- **Security Events** - Failed login attempts
- **Business Metrics** - Fault resolution rates

## 🚀 **Roadmap**

### **Q1 2025**
- ✅ Enterprise Authentication System
- ✅ HTTPS/SSL Production Deployment
- ✅ Admin Panel & User Management
- 🔄 Advanced Audit Logging
- 🔄 Multi-tenant Architecture

### **Q2 2025**
- 📋 Advanced Reporting System
- 📋 API Rate Limiting
- 📋 Advanced Security (2FA)
- 📋 Performance Optimization

### **Q3 2025**
- 📋 Mobile Application
- 📋 Real-time Notifications
- 📋 Advanced Analytics
- 📋 Integration APIs

## 🤝 **Support & Contact**

### **Technical Support**
- **Developer**: M.S.P Development Team
- **Domain**: `maintencesp.com`
- **Platform**: Enterprise Fiber Management System

### **Security**
- **SSL**: Let's Encrypt
- **Authentication**: Enterprise-grade
- **Compliance**: Data protection ready
- **Audit**: Comprehensive logging

---

## 🏆 **Project Status**

**✅ Production Ready** - Enterprise deployment active
**🔐 Security Hardened** - Multiple security layers
**🌐 HTTPS Enabled** - SSL/TLS encryption
**👥 Multi-user** - Role-based access control
**📊 Monitoring** - Comprehensive logging
**🚀 Scalable** - Multi-region architecture

---

**Last Updated**: July 2025  
**Version**: 2.0 Enterprise  
**Status**: Production Active  
**Domain**: https://maintencesp.com