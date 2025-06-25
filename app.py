import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify, send_file, Response
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd
import simplekml
from io import BytesIO
import zipfile
import locale
from ai_integration import FiberArizaAI
import requests
from ai_config import AI_CONFIG
from datetime import datetime, timezone, timedelta
from sqlalchemy import func

# Türkçe locale ayarla
try:
    locale.setlocale(locale.LC_TIME, 'tr_TR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'turkish')
    except:
        pass

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# SQLAlchemy ve Migrate nesnelerini ekle
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fiberariza.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
ai = FiberArizaAI()
insights = ai.generate_dashboard_insights()
OLLAMA_URL = "http://localhost:11434"
AI_MODEL = "qwen2.5:3b"
rag = None


# Uygulamanın bulunduğu dizinde 'files' klasörü oluştur
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')
os.makedirs(BASE_DIR, exist_ok=True)


class FiberAriza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hafta = db.Column(db.String(10))
    bolge = db.Column(db.String(50))
    bulten_no = db.Column(db.String(20), unique=True, nullable=False)
    il = db.Column(db.String(50))
    guzergah = db.Column(db.String(200))
    lokasyon = db.Column(db.String(100))
    ariza_baslangic = db.Column(db.DateTime)
    ariza_bitis = db.Column(db.DateTime)
    ariza_konsolide = db.Column(db.String(200))
    ariza_kok_neden = db.Column(db.String(200))
    hags_asildi_mi = db.Column(db.String(10))
    refakat_durumu = db.Column(db.String(10))
    servis_etkisi = db.Column(db.String(10))
    ariza_suresi = db.Column(db.String(10))
    # Yeni eklenen alanlar
    kordinat_a = db.Column(db.String(50))
    kordinat_b = db.Column(db.String(50))
    kablo_tipi = db.Column(db.String(50))
    hags_suresi = db.Column(db.String(20))
    kesinti_suresi = db.Column(db.String(20))
    kalici_cozum = db.Column(db.String(10))
    kullanilan_malzeme = db.Column(db.String(200))  # Bu eksikti!
    aciklama = db.Column(db.Text)
    serivs_etkisi = db.Column(db.String(50))  # Typo ile
    refakat_saglandi_mi = db.Column(db.String(10))
    deplase_islah_ihtiyaci = db.Column(db.String(10))
    hasar_tazmin_sureci = db.Column(db.String(10))
    otdr_olcum_bilgileri = db.Column(db.Text)
    etkilenen_servis_bilgileri = db.Column(db.Text)  # Bu eksikti!
    yil = db.Column(db.String(10))

class PlaygroundModule(db.Model):
    """Kullanıcı tarafından oluşturulan modüller"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(200))
    icon = db.Column(db.String(50))
    description = db.Column(db.Text)
    fields = db.Column(db.JSON)
    is_pinned = db.Column(db.Boolean, default=False)  # Menüde göster
    menu_order = db.Column(db.Integer, default=999)    # Menü sırası
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class PlaygroundData(db.Model):
    """Playground modüllerinin verileri - ID manuel girilebilir"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)  # Otomatik artış kapalı
    module_id = db.Column(db.Integer, db.ForeignKey('playground_module.id'), nullable=False)
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    module = db.relationship('PlaygroundModule', backref='records')

def get_rag():
    """RAG'i lazy load et"""
    global rag
    if rag is None:
        try:
            from rag_setup import FiberArizaRAG
            rag = FiberArizaRAG()
        except Exception as e:
            print(f"RAG yüklenemedi: {e}")
            rag = None
    return rag    

def parse_utc_date(date_string):
    """UTC tarihini parse et ve Türkiye saatine çevir"""
    if not date_string:
        return None
    try:
        # UTC'den parse et
        utc_date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        # Türkiye saatine çevir (UTC+3)
        turkey_date = utc_date + timedelta(hours=3)
        return turkey_date.replace(tzinfo=None)  # timezone bilgisini kaldır
    except:
        return datetime.fromisoformat(date_string)

@app.route('/')
def home():
    return redirect(url_for('browse'))

@app.route('/api/ai_insights')
def api_ai_insights():
    return jsonify(insights)

@app.route('/browse/')
@app.route('/browse/<path:subpath>')
def browse(subpath=''):
    try:
        # Güvenlik kontrolü
        target_path = os.path.join(BASE_DIR, subpath)
        target_path = os.path.abspath(target_path)
        
        if not target_path.startswith(os.path.abspath(BASE_DIR)):
            flash("Geçersiz dizin yolu!", "error")
            return redirect(url_for('browse'))
        
        if not os.path.exists(target_path):
            flash("Dizin bulunamadı!", "error")
            return redirect(url_for('browse'))
        
        # Dizin içeriğini listele
        items = []
        for item in os.listdir(target_path):
            item_path = os.path.join(target_path, item)
            items.append({
                'name': item,
                'is_dir': os.path.isdir(item_path),
                'size': os.path.getsize(item_path) if not os.path.isdir(item_path) else 0,
                'modified': os.path.getmtime(item_path)
            })
        
        # Breadcrumb oluştur
        breadcrumbs = []
        parts = subpath.split('/') if subpath else []
        for i in range(len(parts)):
            breadcrumbs.append({
                'name': parts[i],
                'path': '/'.join(parts[:i+1])
            })
        
        parent_dir = '/'.join(parts[:-1]) if parts else ''
        
        total = FiberAriza.query.count()
        return render_template('explorer.html', 
                          items=items,
                          current_path=subpath,
                          breadcrumbs=breadcrumbs,
                          parent_dir=parent_dir,
                          total=total)
    
    except Exception as e:
        flash(f"Hata oluştu: {str(e)}", "error")
        return redirect(url_for('browse'))

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Dosya seçilmedi', 'error')
        return redirect(request.referrer)
    
    file = request.files['file']
    if file.filename == '':
        flash('Dosya seçilmedi', 'error')
        return redirect(request.referrer)
    
    current_path = request.form.get('current_path', '')
    target_path = os.path.join(BASE_DIR, current_path)
    
    if file:
        file.save(os.path.join(target_path, file.filename))
        flash('Dosya başarıyla yüklendi', 'success')
    
    return redirect(request.referrer)

@app.route('/delete', methods=['POST'])
def delete_item():
    item_name = request.form.get('item_name')
    current_path = request.form.get('current_path', '')
    target_path = os.path.join(BASE_DIR, current_path, item_name)
    
    try:
        if os.path.isdir(target_path):
            os.rmdir(target_path)
        else:
            os.remove(target_path)
        flash('Öğe silindi', 'success')
    except Exception as e:
        flash(f'Silme hatası: {str(e)}', 'error')
    
    return redirect(request.referrer)

@app.route('/download/<path:filename>')
def download_file(filename):
    current_path = request.args.get('path', '')
    directory = os.path.join(BASE_DIR, current_path)
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/create_folder', methods=['POST'])
def create_folder():
    folder_name = request.form.get('folder_name')
    current_path = request.form.get('current_path', '')
    target_path = os.path.join(BASE_DIR, current_path, folder_name)
    
    try:
        os.mkdir(target_path)
        flash('Dizin oluşturuldu', 'success')
    except Exception as e:
        flash(f'Hata: {str(e)}', 'error')
    
    return redirect(request.referrer)



@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    if 'excel_file' not in request.files:
        flash('Dosya seçilmedi', 'danger')
        return redirect(url_for('browse'))
    file = request.files['excel_file']
    if file.filename == '':
        flash('Geçersiz dosya', 'danger')
        return redirect(url_for('browse'))

    try:
        import pandas as pd
        df = pd.read_excel(file)
        df.columns = [str(col).strip() for col in df.columns]
        required_columns = [
            'Hafta', 'Bölge', 'Bülten Numarası', 'İL', 'Güzergah', 'Lokasyon',
            'Arıza Başlangıç', 'Arıza Bitiş', 'Arıza Konsolide Kök Neden', 'Arıza Kök Neden',
            'HAGS Aşıldı mı', 'Refakat Durumu', 'Servis Etkisi', 'Arıza Süresi'
        ]
        for col in required_columns:
            if col not in df.columns:
                flash(f"Excel'de '{col}' sütunu eksik!", 'danger')
                return redirect(url_for('browse'))

        existing_nos = {x.bulten_no for x in FiberAriza.query.all()}
        new_count = 0

        def parse_date(val):
            if pd.isnull(val):
                return None
            try:
                # Türkçe ay isimlerini İngilizce'ye çevir
                tr_months = {
                    'Ocak': 'January', 'Şubat': 'February', 'Mart': 'March',
                    'Nisan': 'April', 'Mayıs': 'May', 'Haziran': 'June',
                    'Temmuz': 'July', 'Ağustos': 'August', 'Eylül': 'September',
                    'Ekim': 'October', 'Kasım': 'November', 'Aralık': 'December'
                }
                val_str = str(val)
                for tr, en in tr_months.items():
                    val_str = val_str.replace(tr, en)
                return pd.to_datetime(val_str, format='%d %B %Y %H:%M:%S')
            except Exception:
                try:
                    return pd.to_datetime(val)
                except Exception:
                    return None

        for _, row in df.iterrows():
            bulten_no = str(row.get('Bülten Numarası', '')).strip()
            if not bulten_no or bulten_no in existing_nos:
                continue

            new_ariza = FiberAriza(
                hafta=row.get('Hafta', ''),
                bolge=row.get('Bölge', ''),
                bulten_no=bulten_no,
                il=row.get('İL', ''),
                guzergah=row.get('Güzergah', ''),
                lokasyon=row.get('Lokasyon', ''),
                ariza_baslangic=parse_date(row.get('Arıza Başlangıç')),
                ariza_bitis=parse_date(row.get('Arıza Bitiş')),
                ariza_konsolide=row.get('Arıza Konsolide Kök Neden', ''),
                ariza_kok_neden=row.get('Arıza Kök Neden', ''),
                hags_asildi_mi=row.get('HAGS Aşıldı mı', ''),
                refakat_durumu=row.get('Refakat Durumu', ''),
                servis_etkisi=row.get('Servis Etkisi', ''),
                ariza_suresi=row.get('Arıza Süresi', ''),
                # 9 yeni alanı boş bırak
                kordinat_a='',
                kordinat_b='',
                serivs_etkisi='',
                kablo_tipi='',
                hags_suresi='',
                kesinti_suresi='',
                kalici_cozum='',
                kullanilan_malzeme='',
                aciklama=''
            )
            db.session.add(new_ariza)
            new_count += 1

        db.session.commit()
        flash(f'{new_count} yeni kayıt başarıyla eklendi', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'danger')
    return redirect(url_for('browse'))

@app.route('/dashboard')
def dashboard():
    total = FiberAriza.query.count()
    incomplete = FiberAriza.query.filter(
        (FiberAriza.kordinat_a == '') |
        (FiberAriza.kalici_cozum == '')
    ).count()
    arizalar = FiberAriza.query.order_by(FiberAriza.ariza_baslangic.desc()).limit(10).all()
    return render_template('dashboard.html',
                         total=total,
                         incomplete=incomplete,
                         arizalar=arizalar)

@app.route('/delete_ariza/<int:id>', methods=['POST'])
def delete_ariza(id):
    ariza = FiberAriza.query.get_or_404(id)
    try:
        db.session.delete(ariza)
        db.session.commit()
        flash('Kayıt başarıyla silindi', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'danger')
    return redirect(url_for('browse'))

@app.route('/api/arizalar')
def api_arizalar():
    # Pagination parametrelerini kontrol et
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', type=int)
    
    # Eğer pagination parametreleri yoksa, tüm kayıtları döndür (mevcut davranış)
    if page is None or per_page is None:
        arizalar = FiberAriza.query.all()
        return jsonify([{
            'id': a.id,
            'hafta': a.hafta,
            'bolge': a.bolge,
            'bultenNo': a.bulten_no,
            'il': a.il,
            'guzergah': a.guzergah,
            'lokasyon': a.lokasyon,
            'arizaBaslangic': a.ariza_baslangic.isoformat() if a.ariza_baslangic else '',
            'arizaBitis': a.ariza_bitis.isoformat() if a.ariza_bitis else '',
            'arizaKonsolide': a.ariza_konsolide,
            'arizaKokNeden': a.ariza_kok_neden,
            'hagsAsildi': a.hags_asildi_mi,
            'refakatDurumu': a.refakat_durumu,
            'servisEtkisi': a.servis_etkisi,
            'arizaSuresi': a.ariza_suresi,
            'kordinatA': a.kordinat_a,
            'kordinatB': a.kordinat_b,
            'etkilenenServisBilgileri': a.etkilenen_servis_bilgileri,
            'kabloTipi': a.kablo_tipi,
            'hagsSuresi': a.hags_suresi,
            'kesintiSuresi': a.kesinti_suresi,
            'kaliciCozum': a.kalici_cozum,
            'kullanilanMalzeme': a.kullanilan_malzeme,
            'aciklama': a.aciklama,
            'refakatSaglandiMi': a.refakat_saglandi_mi,
            'deplaseIslahIhtiyaci': a.deplase_islah_ihtiyaci,
            'hasarTazminSureci': a.hasar_tazmin_sureci,
            'otdrOlcumBilgileri': a.otdr_olcum_bilgileri,
            'yil': a.yil
        } for a in arizalar])
    
    # Pagination parametreleri varsa, paginated response döndür
    pagination = FiberAriza.query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return jsonify({
        'data': [{
            'id': a.id,
            'hafta': a.hafta,
            'bolge': a.bolge,
            'bultenNo': a.bulten_no,
            'il': a.il,
            'guzergah': a.guzergah,
            'lokasyon': a.lokasyon,
            'arizaBaslangic': a.ariza_baslangic.isoformat() if a.ariza_baslangic else '',
            'arizaBitis': a.ariza_bitis.isoformat() if a.ariza_bitis else '',
            'arizaKonsolide': a.ariza_konsolide,
            'arizaKokNeden': a.ariza_kok_neden,
            'hagsAsildi': a.hags_asildi_mi,
            'refakatDurumu': a.refakat_durumu,
            'servisEtkisi': a.servis_etkisi,
            'arizaSuresi': a.ariza_suresi,
            'kordinatA': a.kordinat_a,
            'kordinatB': a.kordinat_b,
            'etkilenenServisBilgileri': a.etkilenen_servis_bilgileri,
            'kabloTipi': a.kablo_tipi,
            'hagsSuresi': a.hags_suresi,
            'kesintiSuresi': a.kesinti_suresi,
            'kaliciCozum': a.kalici_cozum,
            'kullanilanMalzeme': a.kullanilan_malzeme,
            'aciklama': a.aciklama,
            'refakatSaglandiMi': a.refakat_saglandi_mi,
            'deplaseIslahIhtiyaci': a.deplase_islah_ihtiyaci,
            'hasarTazminSureci': a.hasar_tazmin_sureci,
            'otdrOlcumBilgileri': a.otdr_olcum_bilgileri,
            'yil': a.yil
        } for a in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page
    })

@app.route('/api/ariza', methods=['POST'])
def api_add_ariza():
    data = request.get_json()
    
    # Debug için
    app.logger.info(f"POST - Gelen veri: {data}")
    
    try:
        # Bülten numarası kontrolü
        existing = FiberAriza.query.filter_by(bulten_no=data.get('bultenNo')).first()
        if existing:
            return jsonify({'error': 'Bu Bülten Numarası zaten mevcut!'}), 400
        
        ariza = FiberAriza(
            hafta=data.get('hafta'),
            bolge=data.get('bolge'),
            bulten_no=data.get('bultenNo'),
            il=data.get('il'),
            guzergah=data.get('guzergah'),
            lokasyon=data.get('lokasyon'),
            ariza_baslangic=datetime.fromisoformat(data.get('baslangicTarihi')) if data.get('baslangicTarihi') else None,
            ariza_bitis=datetime.fromisoformat(data.get('bitisTarihi')) if data.get('bitisTarihi') else None,
            ariza_konsolide=data.get('arizaKonsolide'),
            ariza_kok_neden=data.get('kokNeden'),
            hags_asildi_mi=data.get('hags'),
            refakat_durumu=data.get('refakatDurumu'),
            servis_etkisi=data.get('servisEtkisi'),
            ariza_suresi=data.get('arizaSuresi'),
            # Son 14 alan
            kordinat_a=data.get('kordinatA', ''),
            kordinat_b=data.get('kordinatB', ''),
            serivs_etkisi=data.get('serivsEtkisi', ''),  # Eski alan (typo ile)
            etkilenen_servis_bilgileri=data.get('etkilenenServisBilgileri', ''),  # Yeni alan
            kablo_tipi=data.get('kabloTipi', ''),
            hags_suresi=data.get('hagsSuresi', ''),
            kesinti_suresi=data.get('kesintiSuresi', ''),
            kalici_cozum=data.get('kaliciCozum', ''),
            kullanilan_malzeme=data.get('kullanilanMalzeme', ''),
            aciklama=data.get('aciklama', ''),
            refakat_saglandi_mi=data.get('refakatSaglandiMi', ''),
            deplase_islah_ihtiyaci=data.get('deplaseIslahIhtiyaci', ''),
            hasar_tazmin_sureci=data.get('hasarTazminSureci', ''),
            otdr_olcum_bilgileri=data.get('otdrOlcumBilgileri', ''),
            yil=data.get('yil', str(datetime.now().year))
        )
        
        db.session.add(ariza)
        db.session.commit()
        
        return jsonify({'status': 'ok', 'id': ariza.id}), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Arıza ekleme hatası: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/ariza/<int:id>', methods=['PUT'])
def api_update_ariza(id):
    data = request.get_json()
    ariza = FiberAriza.query.get_or_404(id)
    
    # Debug için
    app.logger.info(f"PUT - Gelen veri: {data}")
    
    # Kendi ID'sini hariç tutarak kontrol et
    existing = FiberAriza.query.filter(
        FiberAriza.bulten_no == data.get('bultenNo'),
        FiberAriza.id != id
    ).first()
    
    if existing:
        return jsonify({'error': 'Bu Bülten Numarası ile başka bir kayıt var!'}), 400

    try:
        # İlk 14 alan
        ariza.hafta = data.get('hafta')
        ariza.bolge = data.get('bolge')
        ariza.bulten_no = data.get('bultenNo')
        ariza.il = data.get('il')
        ariza.guzergah = data.get('guzergah')
        ariza.lokasyon = data.get('lokasyon')
        ariza.ariza_baslangic = parse_utc_date(data.get('baslangicTarihi'))
        ariza.ariza_bitis = parse_utc_date(data.get('bitisTarihi'))
        ariza.ariza_konsolide = data.get('arizaKonsolide')
        ariza.ariza_kok_neden = data.get('kokNeden')
        ariza.hags_asildi_mi = data.get('hags')
        ariza.refakat_durumu = data.get('refakatDurumu')
        ariza.servis_etkisi = data.get('servisEtkisi')
        ariza.ariza_suresi = data.get('arizaSuresi')
        
        # Son 14 alan
        ariza.kordinat_a = data.get('kordinatA', '')
        ariza.kordinat_b = data.get('kordinatB', '')
        ariza.serivs_etkisi = data.get('serivsEtkisi', '')  # Eski alan
        ariza.etkilenen_servis_bilgileri = data.get('etkilenenServisBilgileri', '')  # Yeni alan
        ariza.kablo_tipi = data.get('kabloTipi', '')
        ariza.hags_suresi = data.get('hagsSuresi', '')
        ariza.kesinti_suresi = data.get('kesintiSuresi', '')
        ariza.kalici_cozum = data.get('kaliciCozum', '')
        ariza.kullanilan_malzeme = data.get('kullanilanMalzeme', '')
        ariza.aciklama = data.get('aciklama', '')
        ariza.refakat_saglandi_mi = data.get('refakatSaglandiMi', '')
        ariza.deplase_islah_ihtiyaci = data.get('deplaseIslahIhtiyaci', '')
        ariza.hasar_tazmin_sureci = data.get('hasarTazminSureci', '')
        ariza.otdr_olcum_bilgileri = data.get('otdrOlcumBilgileri', '')
        
        db.session.commit()
        return jsonify({'status': 'ok', 'message': 'Güncelleme başarılı'})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Güncelleme hatası: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/filter_data')
def api_filter_data():
    """Filtre dropdown'ları için unique değerleri döndür"""
    try:
        # Unique bölgeler
        bolgeler = db.session.query(FiberAriza.bolge).distinct().order_by(FiberAriza.bolge).all()
        bolgeler = [b[0] for b in bolgeler if b[0]]  # None değerleri filtrele
        
        # Unique iller
        iller = db.session.query(FiberAriza.il).distinct().order_by(FiberAriza.il).all()
        iller = [i[0] for i in iller if i[0]]  # None değerleri filtrele
        
        return jsonify({
            'bolgeler': bolgeler,
            'iller': iller
        })
    except Exception as e:
        app.logger.error(f"Filter data hatası: {str(e)}")
        return jsonify({'bolgeler': [], 'iller': []}), 500

@app.route('/api/ariza/<int:id>', methods=['DELETE'])
def api_delete_ariza(id):
    ariza = FiberAriza.query.get_or_404(id)
    db.session.delete(ariza)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.template_filter('datetimeformat')
def datetimeformat(value):
    import datetime
    return datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M')

@app.route('/download_ariza/<int:id>')
def download_ariza(id):
    ariza = FiberAriza.query.get_or_404(id)
    # Burada ariza verisini bir Excel veya CSV dosyası olarak döndür
    import pandas as pd
    from io import BytesIO
    df = pd.DataFrame([{
        'Koordinat A': ariza.kordinat_a,
        'Koordinat B': ariza.kordinat_b,
        # Diğer alanlar...
    }])
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f'ariza_{ariza.id}.xlsx')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_ariza(id):
    ariza = FiberAriza.query.get_or_404(id)
    if request.method == 'POST':
        ariza.kordinat_a = request.form.get('kordinat_a')
        ariza.kordinat_b = request.form.get('kordinat_b')
        # Diğer alanlar...
        db.session.commit()
        flash('Kayıt güncellendi', 'success')
        return redirect(url_for('browse'))
    return render_template('edit.html', ariza=ariza)

# KMZ Export Fonksiyonu
@app.route('/export_kmz/<string:export_type>')
def export_kmz(export_type='all'):
    """
    KMZ dosyası olarak export et
    export_type: 'all', 'solved', 'unsolved', veya ID
    """
    try:
        # Verileri filtrele
        if export_type == 'all':
            arizalar = FiberAriza.query.all()
            filename = 'tum_arizalar.kmz'
        elif export_type == 'solved':
            arizalar = FiberAriza.query.filter(FiberAriza.kalici_cozum == 'Evet').all()
            filename = 'cozulen_arizalar.kmz'
        elif export_type == 'unsolved':
            arizalar = FiberAriza.query.filter(
                (FiberAriza.kalici_cozum != 'Evet') | (FiberAriza.kalici_cozum == None)
            ).all()
            filename = 'cozulmemis_arizalar.kmz'
        else:
            # Tek bir arıza
            ariza = FiberAriza.query.get_or_404(int(export_type))
            arizalar = [ariza]
            filename = f'ariza_{ariza.bulten_no}.kmz'
        
        # KML oluştur
        kml = simplekml.Kml()
        
        # Stiller tanımla
        solved_style = simplekml.Style()
        solved_style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/icons/green-dot.png'
        
        unsolved_style = simplekml.Style()
        unsolved_style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
        
        for ariza in arizalar:
            if ariza.kordinat_a and ariza.kordinat_b:
                try:
                    # Koordinatları parse et
                    lat = float(ariza.kordinat_a.replace(',', '.'))
                    lon = float(ariza.kordinat_b.replace(',', '.'))
                    
                    # Placemark oluştur
                    pnt = kml.newpoint(name=f"Arıza #{ariza.bulten_no}")
                    pnt.coords = [(lon, lat)]
                    
                    # Stil ata
                    if ariza.kalici_cozum == 'Evet':
                        pnt.style = solved_style
                    else:
                        pnt.style = unsolved_style
                    
                    # Açıklama ekle
                    description = f"""
                    <![CDATA[
                    <b>Bülten No:</b> {ariza.bulten_no}<br>
                    <b>Hafta:</b> {ariza.hafta}<br>
                    <b>Bölge:</b> {ariza.bolge}<br>
                    <b>İl:</b> {ariza.il}<br>
                    <b>Güzergah:</b> {ariza.guzergah}<br>
                    <b>Lokasyon:</b> {ariza.lokasyon}<br>
                    <b>Başlangıç:</b> {ariza.ariza_baslangic}<br>
                    <b>Bitiş:</b> {ariza.ariza_bitis}<br>
                    <b>Kök Neden:</b> {ariza.ariza_kok_neden}<br>
                    <b>Kalıcı Çözüm:</b> {ariza.kalici_cozum}<br>
                    <b>Açıklama:</b> {ariza.aciklama or 'Yok'}<br>
                    ]]>
                    """
                    pnt.description = description
                    
                except ValueError:
                    # Geçersiz koordinat
                    continue
        
        # KMZ olarak kaydet
        output = BytesIO()
        kml.savekmz(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.google-earth.kmz',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'KMZ export hatası: {str(e)}', 'danger')
        return redirect(url_for('browse'))

# Harita API endpoint'i
@app.route('/api/map_data')
def api_map_data():
    """Harita için arıza verilerini döndür (filtreli)"""
    bolge = request.args.get('bolge')
    kalici_cozum = request.args.get('kalici_cozum')
    query = FiberAriza.query.filter(
        FiberAriza.kordinat_a != '',
        FiberAriza.kordinat_b != ''
    )
    if bolge:
        query = query.filter_by(bolge=bolge)
    if kalici_cozum:
        query = query.filter_by(kalici_cozum=kalici_cozum)
    arizalar = query.all()
    markers = []
    for ariza in arizalar:
        try:
            lat = float(ariza.kordinat_a.replace(',', '.'))
            lon = float(ariza.kordinat_b.replace(',', '.'))
            markers.append({
                'id': ariza.id,
                'lat': lat,
                'lng': lon,
                'title': f"Arıza #{ariza.bulten_no}",
                'bultenNo': ariza.bulten_no,
                'hafta': ariza.hafta,
                'bolge': ariza.bolge,
                'il': ariza.il,
                'guzergah': ariza.guzergah,
                'lokasyon': ariza.lokasyon,
                'baslangic': ariza.ariza_baslangic.isoformat() if ariza.ariza_baslangic else '',
                'bitis': ariza.ariza_bitis.isoformat() if ariza.ariza_bitis else '',
                'kokNeden': ariza.ariza_kok_neden,
                'kaliciCozum': ariza.kalici_cozum,
                'aciklama': ariza.aciklama
            })
        except ValueError:
            continue
    return jsonify(markers)

# Excel Export fonksiyonu (tüm data)
@app.route('/export_excel_all')
def export_excel_all():
    """Tüm verileri Excel olarak export et"""
    arizalar = FiberAriza.query.all()
    
    data = []
    for ariza in arizalar:
        data.append({
            'Hafta': ariza.hafta,
            'Bölge': ariza.bolge,
            'Bülten Numarası': ariza.bulten_no,
            'İl': ariza.il,
            'Güzergah': ariza.guzergah,
            'KORDİNAT A': ariza.kordinat_a,
            'KORDİNAT B': ariza.kordinat_b,
            'ETKİLENEN SERVİS BİLGİLERİ': ariza.serivs_etkisi,
            'Lokasyon': ariza.lokasyon,
            'Arıza Başlangıç': ariza.ariza_baslangic.strftime('%d %B %Y %H:%M:%S') if ariza.ariza_baslangic else '',
            'Arıza Bitiş': ariza.ariza_bitis.strftime('%d %B %Y %H:%M:%S') if ariza.ariza_bitis else '',
            'KABLO TİPİ': ariza.kablo_tipi,
            'HAGS SÜRESİ': ariza.hags_suresi,
            'KESİNTİ SÜRESİ': ariza.kesinti_suresi,
            'Arıza Konsolide Kök Neden': ariza.ariza_konsolide,
            'Arıza Kök Neden': ariza.ariza_kok_neden,
            'HAGS Aşıldı mı?': ariza.hags_asildi_mi,
            'Refakat Durumu': ariza.refakat_durumu,
            'Servis Etkisi': ariza.servis_etkisi,
            'Arıza Süresi': ariza.ariza_suresi,
            'KALICI ÇÖZÜM SAĞLANDI': ariza.kalici_cozum,
            'KULLANILAN MALZEME': ariza.kullanilan_malzeme,
            'AÇIKLAMA': ariza.aciklama
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Fiber Arızalar', index=False)
        
        # Sütun genişliklerini ayarla
        worksheet = writer.sheets['Fiber Arızalar']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'fiber_arizalar_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    )

@app.route('/export_excel_custom', methods=['POST'])
def export_excel_custom():
    # Kullanıcıdan seçili başlıkları al
    selected_fields = request.json.get('fields', [])
    arizalar = FiberAriza.query.all()
    data = []
    for ariza in arizalar:
        row = {}
        for field in selected_fields:
            row[field] = getattr(ariza, field, '')
        data.append(row)
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Fiber Arızalar', index=False)
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'fiber_arizalar_custom_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    )

@app.route('/api/arizalar_filtered')
def api_arizalar_filtered():
    # Örnek: ?bolge=Bursa&kalici_cozum=Evet
    query = FiberAriza.query
    bolge = request.args.get('bolge')
    kalici_cozum = request.args.get('kalici_cozum')
    if bolge:
        query = query.filter_by(bolge=bolge)
    if kalici_cozum:
        query = query.filter_by(kalici_cozum=kalici_cozum)
    arizalar = query.all()
    return jsonify([{
        'id': a.id,
        'hafta': a.hafta,
        'bolge': a.bolge,
        'bultenNo': a.bulten_no,
        'il': a.il,
        'guzergah': a.guzergah,
        'kordinatA': a.kordinat_a,
        'kordinatB': a.kordinat_b,
        'servisEtkisi': a.serivs_etkisi,
        'lokasyon': a.lokasyon,
        'arizaBaslangic': a.ariza_baslangic.isoformat() if a.ariza_baslangic else '',
        'arizaBitis': a.ariza_bitis.isoformat() if a.ariza_bitis else '',
        'kabloTipi': a.kablo_tipi,
        'hagsSuresi': a.hags_suresi,
        'kesintiSuresi': a.kesinti_suresi,
        'arizaKonsolide': a.ariza_konsolide,
        'arizaKokNeden': a.ariza_kok_neden,
        'hagsAsildi': a.hags_asildi_mi,
        'refakatDurumu': a.refakat_durumu,
        'servisEtkiDurum': a.servis_etkisi,
        'arizaSuresi': a.ariza_suresi,
        'kaliciCozum': a.kalici_cozum,
        'kullanilanMalzeme': a.kullanilan_malzeme,
        'aciklama': a.aciklama
    } for a in arizalar])

@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze():
    """AI ile arıza analizi"""
    data = request.get_json()
    prompt = data.get('prompt', '')
    
    # Veritabanı context'i ekle
    total_records = FiberAriza.query.count()
    hags_count = FiberAriza.query.filter_by(hags_asildi_mi='Evet').count()
    solved_count = FiberAriza.query.filter_by(kalici_cozum='Evet').count()
    
    context = f"""
    Fiber optik arıza takip sistemi verileri:
    - Toplam arıza: {total_records}
    - HAGS aşan: {hags_count} (%{(hags_count/total_records*100) if total_records > 0 else 0:.1f})
    - Çözülen: {solved_count} (%{(solved_count/total_records*100) if total_records > 0 else 0:.1f})
    
    Kullanıcı sorusu: {prompt}
    """
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": AI_MODEL,
                "prompt": context,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            ai_response = response.json().get("response", "")
            return jsonify({
                "success": True,
                "response": ai_response,
                "model": AI_MODEL
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Model hatası: {response.status_code}"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/insights')
def ai_insights():
    """Dashboard için AI içgörüleri"""
    # Veritabanı istatistikleri
    total = FiberAriza.query.count()
    
    # Bölgesel analiz
    from sqlalchemy import func
    bolge_stats = db.session.query(
        FiberAriza.bolge,
        func.count(FiberAriza.id).label('count')
    ).group_by(FiberAriza.bolge).all()
    
    # En riskli bölgeler
    risk_areas = []
    for bolge, count in bolge_stats:
        if count > 5:  # Eşik değer
            risk_areas.append({
                "area": bolge,
                "risk_score": min(count / 10, 1.0),
                "failure_count": count
            })
    
    # AI tahminleri
    predictions = []
    if risk_areas:
        predictions.append({
            "type": "high_risk_warning",
            "message": f"{len(risk_areas)} bölgede yüksek arıza riski tespit edildi",
            "areas": [area['area'] for area in risk_areas[:3]]
        })
    
    # HAGS analizi
    hags_count = FiberAriza.query.filter_by(hags_asildi_mi='Evet').count()
    if total > 0 and (hags_count / total) > 0.2:
        predictions.append({
            "type": "hags_alert",
            "message": f"HAGS aşım oranı %{(hags_count/total*100):.1f} - Kritik seviyede",
            "recommendation": "Ekip sayısını artırın veya süreç optimizasyonu yapın"
        })
    
    return jsonify({
        "total_records": total,
        "risk_areas": risk_areas,
        "predictions": predictions,
        "generated_at": datetime.now().isoformat()
    })

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """RAG destekli AI chat"""
    data = request.get_json()
    message = data.get('message', '')
    
    # RAG context'i al
    context = ""
    try:
        from rag_setup import FiberArizaRAG
        rag = FiberArizaRAG()
        context = rag.get_context_for_llm(message)
    except Exception as e:
        print(f"RAG hatası: {e}")
        context = ""
    
    # Veritabanı istatistikleri
    total_ariza = FiberAriza.query.count()
    hags_asan = FiberAriza.query.filter_by(hags_asildi_mi='Evet').count()
    cozulen = FiberAriza.query.filter_by(kalici_cozum='Evet').count()
    
    # Bölge istatistikleri ekle
    from sqlalchemy import func
    bolge_stats = db.session.query(
        FiberAriza.bolge,
        func.count(FiberAriza.id).label('count')
    ).group_by(FiberAriza.bolge).all()
    
    bolge_info = "\nBölgesel Dağılım:\n"
    for bolge, count in bolge_stats[:5]:  # İlk 5 bölge
        bolge_info += f"- {bolge}: {count} arıza\n"
    
    full_prompt = f"""Sen bir fiber optik arıza takip sistemi asistanısın.
    
    GERÇEK VERİTABANI İSTATİSTİKLERİ:
    - Toplam arıza sayısı: {total_ariza}
    - HAGS süresini aşan arıza sayısı: {hags_asan}
    - Çözülen arıza sayısı: {cozulen}
    - Çözülmeyen arıza sayısı: {total_ariza - cozulen}
    
    {bolge_info}
    
    RAG ARAMA SONUÇLARI:
    {context}
    
    FIBER TERMİNOLOJİSİ:
    - HAGS: Hizmet Alım Garanti Süresi (arızanın çözülmesi için maksimum süre)
    - FTTB: Fiber to the Building (Binaya kadar fiber)
    - DDO: Dijital Dağıtım Ofisi
    - OTDR: Optical Time Domain Reflectometer
    - Deplase: Kablo güzergahının değiştirilmesi
    
    Kullanıcı sorusu: {message}
    
    KURALLLAR:
    1. SADECE yukarıda verilen gerçek verileri kullan
    2. Kesinlikle uydurma sayı veya istatistik kullanma
    3. Eğer spesifik bir veri yoksa "Bu konuda veritabanında bilgi bulunamadı" de
    4. Türkçe olarak net ve anlaşılır cevap ver
    """
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": AI_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "temperature": 0.2  # Daha deterministik cevaplar
            },
            timeout=60
        )
        
        if response.status_code == 200:
            ai_response = response.json().get("response", "")
            return jsonify({
                "success": True,
                "message": ai_response
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Model hatası: {response.status_code}"
            }), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Hata: {str(e)}"
        }), 500

@app.route('/api/ai/report/<string:report_type>')
def ai_generate_report(report_type):
    """AI ile otomatik rapor üretimi"""
    
    if report_type == 'weekly':
        # Haftalık rapor
        prompt = """
        Haftalık fiber arıza raporu hazırla. Şunları içersin:
        1. Genel durum özeti
        2. En çok arıza olan bölgeler
        3. HAGS performansı
        4. Öneriler
        """
    elif report_type == 'risk':
        # Risk analizi raporu
        prompt = """
        Risk analizi raporu hazırla:
        1. Yüksek riskli bölgeler
        2. Tekrarlayan arıza nedenleri
        3. Önleyici tedbirler
        4. Yatırım önerileri
        """
    else:
        return jsonify({"error": "Geçersiz rapor tipi"}), 400
    
    # Veritabanından veri topla
    stats = {
        "total": FiberAriza.query.count(),
        "solved": FiberAriza.query.filter_by(kalici_cozum='Evet').count(),
        "hags_exceeded": FiberAriza.query.filter_by(hags_asildi_mi='Evet').count()
    }
    
    full_prompt = f"""
    {prompt}
    
    Veriler:
    - Toplam arıza: {stats['total']}
    - Çözülen: {stats['solved']}
    - HAGS aşan: {stats['hags_exceeded']}
    
    Profesyonel bir rapor formatında yaz.
    """
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": AI_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "temperature": 0.3  # Daha tutarlı çıktı için
            },
            timeout=60  # Rapor için daha uzun timeout
        )
        
        if response.status_code == 200:
            report = response.json().get("response", "")
            
            # Raporu kaydet
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_report_{report_type}_{timestamp}.txt"
            filepath = os.path.join("files", filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            
            return jsonify({
                "success": True,
                "report": report,
                "filename": filename
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Dashboard'a AI widget eklemek için
@app.route('/api/ai/widget')
def ai_widget_data():
    """Dashboard AI widget verisi"""
    # Basit tahminler
    total = FiberAriza.query.count()
    
    # Son 7 günün arıza ortalaması
    from datetime import datetime, timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_count = FiberAriza.query.filter(
        FiberAriza.ariza_baslangic >= seven_days_ago
    ).count()
    
    daily_avg = recent_count / 7 if recent_count > 0 else 0
    
    # Basit tahmin
    next_week_prediction = int(daily_avg * 7 * 1.1)  # %10 artış tahmini
    
    return jsonify({
        "current_week": recent_count,
        "daily_average": round(daily_avg, 1),
        "next_week_prediction": next_week_prediction,
        "trend": "increasing" if daily_avg > 1 else "stable",
        "confidence": 0.75
    })

@app.route('/playground')
def playground():
    return render_template('playground.html')

@app.route('/api/playground/modules', methods=['GET'])
def api_get_playground_modules():
    """Tüm playground modüllerini getir"""
    modules = PlaygroundModule.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'display_name': m.display_name,
        'icon': m.icon,
        'description': m.description,
        'fields': m.fields,
        'is_pinned': m.is_pinned,  # Bu satır eksikti!
        'created_at': m.created_at.isoformat()
    } for m in modules])

@app.route('/api/playground/modules', methods=['POST'])
def api_create_playground_module():
    """Yeni playground modülü oluştur"""
    data = request.get_json()
    
    # Modül adı kontrolü
    existing = PlaygroundModule.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'error': 'Bu modül adı zaten kullanılıyor'}), 400
    
    try:
        module = PlaygroundModule(
            name=data['name'],
            display_name=data['display_name'],
            icon=data.get('icon', 'fas fa-puzzle-piece'),
            description=data.get('description', ''),
            fields=data['fields']
        )
        db.session.add(module)
        db.session.commit()
        
        return jsonify({'id': module.id, 'message': 'Modül oluşturuldu'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/playground/module/<module_name>')
def playground_module(module_name):
    """Playground modülü detay sayfası"""
    module = PlaygroundModule.query.filter_by(name=module_name).first_or_404()
    return render_template('playground_module.html', module=module)

@app.route('/api/playground/<module_name>/data', methods=['GET'])
def api_get_playground_data(module_name):
    """Modül verilerini getir"""
    module = PlaygroundModule.query.filter_by(name=module_name).first_or_404()
    
    # Pagination
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', type=int)
    
    query = PlaygroundData.query.filter_by(module_id=module.id)
    
    if page and per_page:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [{'id': d.id, **d.data, 'created_at': d.created_at.isoformat()} 
                    for d in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        })
    else:
        data = query.all()
        return jsonify([{'id': d.id, **d.data, 'created_at': d.created_at.isoformat()} 
                       for d in data])

@app.route('/api/playground/modules/<int:module_id>/toggle-pin', methods=['POST'])
def api_toggle_pin_module(module_id):
    """Modülü menüye sabitle/kaldır"""
    module = PlaygroundModule.query.get_or_404(module_id)
    module.is_pinned = not module.is_pinned
    
    try:
        db.session.commit()
        return jsonify({'is_pinned': module.is_pinned})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/playground/<module_name>/data', methods=['POST'])
def api_create_playground_data(module_name):
    """Modüle veri ekle - manuel ID desteği ile"""
    module = PlaygroundModule.query.filter_by(name=module_name).first_or_404()
    data = request.get_json()
    
    app.logger.info(f"POST data received for {module_name}: {data}")  # Debug log
    
    try:
        # Manuel ID varsa kontrol et
        if 'id' in data and data['id']:
            existing = PlaygroundData.query.get(data['id'])
            if existing:
                return jsonify({'error': f"ID {data['id']} zaten kullanımda!"}), 400
            
            record_id = data.pop('id')
            record = PlaygroundData(
                id=record_id,
                module_id=module.id,
                data=data
            )
        else:
            # Otomatik ID ata
            from sqlalchemy import func
            max_id = db.session.query(func.max(PlaygroundData.id)).scalar() or 0
            record = PlaygroundData(
                id=max_id + 1,
                module_id=module.id,
                data=data
            )
        
        db.session.add(record)
        db.session.commit()
        
        app.logger.info(f"Record created with ID: {record.id}")  # Debug log
        
        return jsonify({'id': record.id, 'message': 'Kayıt eklendi'}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating playground data: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/playground/pinned-modules')
def api_get_pinned_modules():
    """Menüde gösterilecek modülleri getir"""
    modules = PlaygroundModule.query.filter_by(
        is_pinned=True, 
        is_active=True
    ).order_by(PlaygroundModule.menu_order).all()
    
    return jsonify([{
        'name': m.name,
        'display_name': m.display_name,
        'icon': m.icon
    } for m in modules])

@app.route('/api/playground/<module_name>/data/<int:data_id>', methods=['PUT'])
def api_update_playground_data(module_name, data_id):
    """Modül verisini güncelle"""
    module = PlaygroundModule.query.filter_by(name=module_name).first_or_404()
    record = PlaygroundData.query.filter_by(id=data_id, module_id=module.id).first_or_404()
    
    data = request.get_json()
    record.data = data
    record.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'message': 'Güncellendi'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/playground/<module_name>/data/<int:data_id>', methods=['DELETE'])
def api_delete_playground_data(module_name, data_id):
    """Modül verisini sil"""
    module = PlaygroundModule.query.filter_by(name=module_name).first_or_404()
    record = PlaygroundData.query.filter_by(id=data_id, module_id=module.id).first_or_404()
    
    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Silindi'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/playground/<module_name>/export')
def api_export_playground_data(module_name):
    """Modül verilerini Excel olarak export et"""
    module = PlaygroundModule.query.filter_by(name=module_name).first_or_404()
    records = PlaygroundData.query.filter_by(module_id=module.id).all()
    
    # Sütun başlıklarını hazırla
    columns = ['ID']
    for field in module.fields:
        columns.append(field['name'])
    columns.append('Oluşturulma Tarihi')
    columns.append('Güncelleme Tarihi')
    
    # Verileri hazırla
    data_list = []
    for record in records:
        row = [record.id]
        
        # Her alan için veriyi ekle
        for field in module.fields:
            value = record.data.get(field['name'], '')
            row.append(value)
        
        # Tarih alanları
        row.append(record.created_at.strftime('%d.%m.%Y %H:%M'))
        row.append(record.updated_at.strftime('%d.%m.%Y %H:%M') if record.updated_at else '')
        
        data_list.append(row)
    
    # DataFrame oluştur
    df = pd.DataFrame(data_list, columns=columns)
    
    # Excel oluştur
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=module.display_name[:31], index=False)  # Excel sheet adı max 31 karakter
        worksheet = writer.sheets[module.display_name[:31]]
        
        # Sütun genişlikleri
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{module.name}_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    )

@app.route('/api/playground/modules/<int:module_id>', methods=['PUT'])
def api_update_playground_module(module_id):
    """Playground modülünü güncelle"""
    module = PlaygroundModule.query.get_or_404(module_id)
    data = request.get_json()
    
    try:
        # İsim değiştirilmeye çalışılıyorsa kontrol et
        if data['name'] != module.name:
            existing = PlaygroundModule.query.filter_by(name=data['name']).first()
            if existing:
                return jsonify({'error': 'Bu modül adı zaten kullanılıyor'}), 400
        
        module.name = data['name']
        module.display_name = data['display_name']
        module.icon = data.get('icon', 'fas fa-puzzle-piece')
        module.description = data.get('description', '')
        module.fields = data['fields']
        module.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'message': 'Modül güncellendi'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/playground/modules/<int:module_id>', methods=['DELETE'])
def api_delete_playground_module(module_id):
    """Playground modülünü sil"""
    module = PlaygroundModule.query.get_or_404(module_id)
    
    try:
        # Önce modüle ait tüm verileri sil
        PlaygroundData.query.filter_by(module_id=module.id).delete()
        
        # Sonra modülü sil
        db.session.delete(module)
        db.session.commit()
        
        return jsonify({'message': 'Modül ve tüm verileri silindi'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/playground/<module_name>/import', methods=['POST'])
def api_import_playground_data(module_name):
    """Toplu veri import et"""
    module = PlaygroundModule.query.filter_by(name=module_name).first_or_404()
    data_list = request.get_json()
    
    if not isinstance(data_list, list):
        return jsonify({'error': 'Veri listesi bekleniyor'}), 400
    
    success_count = 0
    errors = []
    
    for idx, data in enumerate(data_list):
        try:
            # Manuel ID kontrolü
            if 'id' in data and data['id']:
                record_id = data.pop('id')
                existing = PlaygroundData.query.get(record_id)
                if existing:
                    errors.append(f"Satır {idx + 1}: ID {record_id} zaten mevcut")
                    continue
                    
                record = PlaygroundData(
                    id=record_id,
                    module_id=module.id,
                    data=data
                )
            else:
                # Otomatik ID
                from sqlalchemy import func
                max_id = db.session.query(func.max(PlaygroundData.id)).scalar() or 0
                record = PlaygroundData(
                    id=max_id + success_count + 1,
                    module_id=module.id,
                    data=data
                )
            
            db.session.add(record)
            success_count += 1
            
        except Exception as e:
            errors.append(f"Satır {idx + 1}: {str(e)}")
    
    try:
        db.session.commit()
        return jsonify({
            'success': success_count,
            'errors': errors
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)