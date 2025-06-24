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
    kullanilan_malzeme = db.Column(db.String(200))
    aciklama = db.Column(db.Text)
    serivs_etkisi = db.Column(db.String(50))  # H sütunu için yeni alan
    refakat_saglandi_mi = db.Column(db.String(10))
    deplase_islah_ihtiyaci = db.Column(db.String(10))
    hasar_tazmin_sureci = db.Column(db.String(10))
    otdr_olcum_bilgileri = db.Column(db.Text)
    etkilenen_servis_bilgileri = db.Column(db.Text)  # H sütunu için doğru alan
    yil = db.Column(db.String(10))  # Yıl alanı

class DeplaseIslah(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    yil = db.Column(db.String(10))
    hafta = db.Column(db.String(10))
    ddo = db.Column(db.String(100))
    guzergah = db.Column(db.String(200))
    is_tipi = db.Column(db.String(50))
    kordinat_a = db.Column(db.String(50))
    kordinat_b = db.Column(db.String(50))
    aciklama = db.Column(db.Text)
    durum = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HasarTazmin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bolge = db.Column(db.String(100))
    yazi_no = db.Column(db.String(100))
    tarih = db.Column(db.DateTime)
    asil_firma = db.Column(db.String(200))
    muhaberat_verilis_tarihi = db.Column(db.DateTime)
    taseron = db.Column(db.String(200))
    durumu = db.Column(db.String(50))
    muhaberat_teslim_eden = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FTTBOptimizasyon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    yil = db.Column(db.String(10))
    hafta = db.Column(db.String(10))
    ddo = db.Column(db.String(100))
    statu = db.Column(db.String(100))
    obek = db.Column(db.String(100))
    fttb_ring_name = db.Column(db.String(200))
    lokasyon_id = db.Column(db.String(100))
    ci_name = db.Column(db.String(200))
    aciklama = db.Column(db.Text)
    durum = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class KritikModernizasyon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    yil = db.Column(db.String(10))
    hafta = db.Column(db.String(10))
    ddo = db.Column(db.String(100))
    bulten_no = db.Column(db.String(100))
    lokasyon_id = db.Column(db.String(100))
    is_tipi = db.Column(db.String(200))
    lokasyon = db.Column(db.String(200))
    aciklama = db.Column(db.Text)
    durumu = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    arizalar = FiberAriza.query.all()
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

@app.route('/api/ariza', methods=['POST'])
def api_add_ariza():
    data = request.get_json()
    
    # Field mapping düzeltmesi
    try:
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
            serivs_etkisi=data.get('etkilenenServisBilgileri', ''),  # H sütunu
            kablo_tipi=data.get('kabloTipi', ''),
            hags_suresi=data.get('hagsSuresi', ''),
            kesinti_suresi=data.get('kesintiSuresi', ''),
            kalici_cozum=data.get('kaliciCozum', ''),
            kullanilan_malzeme=data.get('kullanilanMalzeme', ''),
            aciklama=data.get('aciklama', ''),
            # Eksik alanlar
            refakat_saglandi_mi=data.get('refakatSaglandiMi', ''),
            deplase_islah_ihtiyaci=data.get('deplaseIslahIhtiyaci', ''),
            hasar_tazmin_sureci=data.get('hasarTazminSureci', ''),
            otdr_olcum_bilgileri=data.get('otdrOlcumBilgileri', '')
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
    
    # SORUN BURADA ÇÖZÜLDÜ: Kendi ID'sini hariç tutuyoruz
    existing = FiberAriza.query.filter(
        FiberAriza.bulten_no == data.get('bultenNo'),
        FiberAriza.id != id  # Bu satır kritik!
    ).first()
    
    if existing:
        return jsonify({'error': 'Bu Bülten Numarası ile başka bir kayıt var!'}), 400

    ariza.hafta = data.get('hafta')
    ariza.bolge = data.get('bolge')
    ariza.bulten_no = data.get('bultenNo')
    ariza.il = data.get('il')
    ariza.guzergah = data.get('guzergah')
    ariza.kordinat_a = data.get('kordinatA')
    ariza.kordinat_b = data.get('kordinatB')
    ariza.ariza_baslangic = datetime.fromisoformat(data.get('baslangicTarihi')) if data.get('baslangicTarihi') else None
    ariza.ariza_bitis = datetime.fromisoformat(data.get('bitisTarihi')) if data.get('bitisTarihi') else None
    ariza.kablo_tipi = data.get('kabloTipi')
    ariza.ariza_kok_neden = data.get('kokNeden')
    ariza.hags_asildi_mi = data.get('hags')
    ariza.servis_etkisi = data.get('servisEtkisi')
    ariza.ariza_suresi = data.get('arizaSuresi')
    ariza.kalici_cozum = data.get('kaliciCozum')
    ariza.ariza_konsolide = data.get('arizaKonsolide')
    ariza.lokasyon = data.get('lokasyon')
    ariza.refakat_durumu = data.get('refakatDurumu')
    ariza.hags_suresi = data.get('hagsSuresi')
    ariza.kesinti_suresi = data.get('kesintiSuresi')
    ariza.kullanilan_malzeme = data.get('kullanilanMalzeme')
    ariza.aciklama = data.get('aciklama')
    ariza.serivs_etkisi = data.get('serivsEtkisi')
    db.session.commit()
    return jsonify({'status': 'ok'})

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

@app.route('/deplase_islah')
def deplase_islah():
    total = DeplaseIslah.query.count()
    return render_template('deplase_islah.html', total=total)

@app.route('/api/deplase_islah')
def api_deplase_islah():
    deplaseler = DeplaseIslah.query.all()
    return jsonify([{
        'id': d.id,
        'yil': d.yil,
        'hafta': d.hafta,
        'ddo': d.ddo,
        'guzergah': d.guzergah,
        'isTipi': d.is_tipi,
        'kordinatA': d.kordinat_a,
        'kordinatB': d.kordinat_b,
        'aciklama': d.aciklama,
        'durum': d.durum
    } for d in deplaseler])

@app.route('/api/deplase_islah', methods=['POST'])
def api_add_deplase_islah():
    data = request.get_json()
    
    deplase = DeplaseIslah(
        yil=data.get('yil'),
        hafta=data.get('hafta'),
        ddo=data.get('ddo'),
        guzergah=data.get('guzergah'),
        is_tipi=data.get('isTipi'),
        kordinat_a=data.get('kordinatA'),
        kordinat_b=data.get('kordinatB'),
        aciklama=data.get('aciklama'),
        durum=data.get('durum')
    )
    db.session.add(deplase)
    db.session.commit()
    return jsonify({'status': 'ok'}), 201

@app.route('/api/deplase_islah/<int:id>', methods=['PUT'])
def api_update_deplase_islah(id):
    data = request.get_json()
    deplase = DeplaseIslah.query.get_or_404(id)
    
    deplase.yil = data.get('yil')
    deplase.hafta = data.get('hafta')
    deplase.ddo = data.get('ddo')
    deplase.guzergah = data.get('guzergah')
    deplase.is_tipi = data.get('isTipi')
    deplase.kordinat_a = data.get('kordinatA')
    deplase.kordinat_b = data.get('kordinatB')
    deplase.aciklama = data.get('aciklama')
    deplase.durum = data.get('durum')
    deplase.updated_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/deplase_islah/<int:id>', methods=['DELETE'])
def api_delete_deplase_islah(id):
    deplase = DeplaseIslah.query.get_or_404(id)
    db.session.delete(deplase)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/upload_deplase_islah_excel', methods=['POST'])
def upload_deplase_islah_excel():
    if 'excel_file' not in request.files:
        flash('Dosya seçilmedi', 'danger')
        return redirect(url_for('deplase_islah'))
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('Geçersiz dosya', 'danger')
        return redirect(url_for('deplase_islah'))

    try:
        df = pd.read_excel(file)
        df.columns = [str(col).strip() for col in df.columns]
        
        required_columns = ['YIL', 'HAFTA', 'DDO', 'Güzergah', 'İş Tipi', 
                          'KOORDİNAT A', 'KOORDİNAT B', 'AÇIKLAMA', 'DURUM']
        
        for col in required_columns:
            if col not in df.columns:
                flash(f"Excel'de '{col}' sütunu eksik!", 'danger')
                return redirect(url_for('deplase_islah'))
        
        new_count = 0
        for _, row in df.iterrows():
            new_deplase = DeplaseIslah(
                yil=str(row.get('YIL', '')),
                hafta=str(row.get('HAFTA', '')),
                ddo=str(row.get('DDO', '')),
                guzergah=str(row.get('Güzergah', '')),
                is_tipi=str(row.get('İş Tipi', '')),
                kordinat_a=str(row.get('KOORDİNAT A', '')),
                kordinat_b=str(row.get('KOORDİNAT B', '')),
                aciklama=str(row.get('AÇIKLAMA', '')),
                durum=str(row.get('DURUM', ''))
            )
            db.session.add(new_deplase)
            new_count += 1
        
        db.session.commit()
        flash(f'{new_count} yeni kayıt başarıyla eklendi', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'danger')
    
    return redirect(url_for('deplase_islah'))

@app.route('/export_deplase_islah_excel')
def export_deplase_islah_excel():
    deplaseler = DeplaseIslah.query.all()
    
    data = []
    for deplase in deplaseler:
        data.append({
            'YIL': deplase.yil,
            'HAFTA': deplase.hafta,
            'DDO': deplase.ddo,
            'Güzergah': deplase.guzergah,
            'İş Tipi': deplase.is_tipi,
            'KOORDİNAT A': deplase.kordinat_a,
            'KOORDİNAT B': deplase.kordinat_b,
            'AÇIKLAMA': deplase.aciklama,
            'DURUM': deplase.durum
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Deplase Islah', index=False)
        worksheet = writer.sheets['Deplase Islah']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'deplase_islah_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    )


@app.route('/hasar_tazmin')
def hasar_tazmin():
    total = HasarTazmin.query.count()
    return render_template('hasar_tazmin.html', total=total)

@app.route('/api/hasar_tazmin')
def api_hasar_tazmin():
    hasarlar = HasarTazmin.query.all()
    return jsonify([{
        'id': h.id,
        'bolge': h.bolge,
        'yaziNo': h.yazi_no,
        'tarih': h.tarih.isoformat() if h.tarih else '',
        'asilFirma': h.asil_firma,
        'muhaberatVerilisTarihi': h.muhaberat_verilis_tarihi.isoformat() if h.muhaberat_verilis_tarihi else '',
        'taseron': h.taseron,
        'durumu': h.durumu,
        'muhaberatTeslimEden': h.muhaberat_teslim_eden
    } for h in hasarlar])

@app.route('/api/hasar_tazmin', methods=['POST'])
def api_add_hasar_tazmin():
    data = request.get_json()
    
    def parse_date(date_str):
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str)
        except:
            return None
    
    hasar = HasarTazmin(
        bolge=data.get('bolge'),
        yazi_no=data.get('yaziNo'),
        tarih=parse_date(data.get('tarih')),
        asil_firma=data.get('asilFirma'),
        muhaberat_verilis_tarihi=parse_date(data.get('muhaberatVerilisTarihi')),
        taseron=data.get('taseron'),
        durumu=data.get('durumu'),
        muhaberat_teslim_eden=data.get('muhaberatTeslimEden')
    )
    db.session.add(hasar)
    db.session.commit()
    return jsonify({'status': 'ok'}), 201

@app.route('/api/hasar_tazmin/<int:id>', methods=['PUT'])
def api_update_hasar_tazmin(id):
    data = request.get_json()
    hasar = HasarTazmin.query.get_or_404(id)
    
    def parse_date(date_str):
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str)
        except:
            return None
    
    hasar.bolge = data.get('bolge')
    hasar.yazi_no = data.get('yaziNo')
    hasar.tarih = parse_date(data.get('tarih'))
    hasar.asil_firma = data.get('asilFirma')
    hasar.muhaberat_verilis_tarihi = parse_date(data.get('muhaberatVerilisTarihi'))
    hasar.taseron = data.get('taseron')
    hasar.durumu = data.get('durumu')
    hasar.muhaberat_teslim_eden = data.get('muhaberatTeslimEden')
    hasar.updated_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/hasar_tazmin/<int:id>', methods=['DELETE'])
def api_delete_hasar_tazmin(id):
    hasar = HasarTazmin.query.get_or_404(id)
    db.session.delete(hasar)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/upload_hasar_tazmin_excel', methods=['POST'])
def upload_hasar_tazmin_excel():
    if 'excel_file' not in request.files:
        flash('Dosya seçilmedi', 'danger')
        return redirect(url_for('hasar_tazmin'))
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('Geçersiz dosya', 'danger')
        return redirect(url_for('hasar_tazmin'))

    try:
        df = pd.read_excel(file)
        df.columns = [str(col).strip() for col in df.columns]
        
        required_columns = ['BÖLGE', 'YAZI NO', 'TARİH', 'ASIL FİRMA', 
                          'MUHABERAT VERİLİŞ TARİHİ', 'TAŞERON', 'DURUMU', 'MUHABERAT TESLİM EDEN']
        
        for col in required_columns:
            if col not in df.columns:
                flash(f"Excel'de '{col}' sütunu eksik!", 'danger')
                return redirect(url_for('hasar_tazmin'))
        
        def parse_excel_date(val):
            if pd.isnull(val):
                return None
            try:
                return pd.to_datetime(val)
            except:
                return None
        
        new_count = 0
        for _, row in df.iterrows():
            new_hasar = HasarTazmin(
                bolge=str(row.get('BÖLGE', '')),
                yazi_no=str(row.get('YAZI NO', '')),
                tarih=parse_excel_date(row.get('TARİH')),
                asil_firma=str(row.get('ASIL FİRMA', '')),
                muhaberat_verilis_tarihi=parse_excel_date(row.get('MUHABERAT VERİLİŞ TARİHİ')),
                taseron=str(row.get('TAŞERON', '')),
                durumu=str(row.get('DURUMU', '')),
                muhaberat_teslim_eden=str(row.get('MUHABERAT TESLİM EDEN', ''))
            )
            db.session.add(new_hasar)
            new_count += 1
        
        db.session.commit()
        flash(f'{new_count} yeni kayıt başarıyla eklendi', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'danger')
    
    return redirect(url_for('hasar_tazmin'))

@app.route('/export_hasar_tazmin_excel')
def export_hasar_tazmin_excel():
    hasarlar = HasarTazmin.query.all()
    
    data = []
    for hasar in hasarlar:
        data.append({
            'BÖLGE': hasar.bolge,
            'YAZI NO': hasar.yazi_no,
            'TARİH': hasar.tarih.strftime('%d.%m.%Y') if hasar.tarih else '',
            'ASIL FİRMA': hasar.asil_firma,
            'MUHABERAT VERİLİŞ TARİHİ': hasar.muhaberat_verilis_tarihi.strftime('%d.%m.%Y') if hasar.muhaberat_verilis_tarihi else '',
            'TAŞERON': hasar.taseron,
            'DURUMU': hasar.durumu,
            'MUHABERAT TESLİM EDEN': hasar.muhaberat_teslim_eden
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Hasar Tazmin', index=False)
        worksheet = writer.sheets['Hasar Tazmin']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'hasar_tazmin_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    )

@app.route('/fttb_optimizasyon')
def fttb_optimizasyon():
    total = FTTBOptimizasyon.query.count()
    return render_template('fttb_optimizasyon.html', total=total)

@app.route('/api/fttb_optimizasyon')
def api_fttb_optimizasyon():
    fttb_list = FTTBOptimizasyon.query.all()
    return jsonify([{
        'id': f.id,
        'yil': f.yil,
        'hafta': f.hafta,
        'ddo': f.ddo,
        'statu': f.statu,
        'obek': f.obek,
        'fttbRingName': f.fttb_ring_name,
        'lokasyonId': f.lokasyon_id,
        'ciName': f.ci_name,
        'aciklama': f.aciklama,
        'durum': f.durum
    } for f in fttb_list])

@app.route('/api/fttb_optimizasyon', methods=['POST'])
def api_add_fttb_optimizasyon():
    data = request.get_json()
    
    fttb = FTTBOptimizasyon(
        yil=data.get('yil'),
        hafta=data.get('hafta'),
        ddo=data.get('ddo'),
        statu=data.get('statu'),
        obek=data.get('obek'),
        fttb_ring_name=data.get('fttbRingName'),
        lokasyon_id=data.get('lokasyonId'),
        ci_name=data.get('ciName'),
        aciklama=data.get('aciklama'),
        durum=data.get('durum')
    )
    db.session.add(fttb)
    db.session.commit()
    return jsonify({'status': 'ok'}), 201

@app.route('/api/fttb_optimizasyon/<int:id>', methods=['PUT'])
def api_update_fttb_optimizasyon(id):
    data = request.get_json()
    fttb = FTTBOptimizasyon.query.get_or_404(id)
    
    fttb.yil = data.get('yil')
    fttb.hafta = data.get('hafta')
    fttb.ddo = data.get('ddo')
    fttb.statu = data.get('statu')
    fttb.obek = data.get('obek')
    fttb.fttb_ring_name = data.get('fttbRingName')
    fttb.lokasyon_id = data.get('lokasyonId')
    fttb.ci_name = data.get('ciName')
    fttb.aciklama = data.get('aciklama')
    fttb.durum = data.get('durum')
    fttb.updated_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/fttb_optimizasyon/<int:id>', methods=['DELETE'])
def api_delete_fttb_optimizasyon(id):
    fttb = FTTBOptimizasyon.query.get_or_404(id)
    db.session.delete(fttb)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/upload_fttb_optimizasyon_excel', methods=['POST'])
def upload_fttb_optimizasyon_excel():
    if 'excel_file' not in request.files:
        flash('Dosya seçilmedi', 'danger')
        return redirect(url_for('fttb_optimizasyon'))
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('Geçersiz dosya', 'danger')
        return redirect(url_for('fttb_optimizasyon'))

    try:
        df = pd.read_excel(file)
        df.columns = [str(col).strip() for col in df.columns]
        
        required_columns = ['YIL', 'HAFTA', 'DDO', 'STATÜ', 'ÖBEK', 
                          'FTTB RİNG NAME', 'LOKASYON ID', 'CI NAME', 'AÇIKLAMA', 'DURUM']
        
        for col in required_columns:
            if col not in df.columns:
                flash(f"Excel'de '{col}' sütunu eksik!", 'danger')
                return redirect(url_for('fttb_optimizasyon'))
        
        new_count = 0
        for _, row in df.iterrows():
            new_fttb = FTTBOptimizasyon(
                yil=str(row.get('YIL', '')),
                hafta=str(row.get('HAFTA', '')),
                ddo=str(row.get('DDO', '')),
                statu=str(row.get('STATÜ', '')),
                obek=str(row.get('ÖBEK', '')),
                fttb_ring_name=str(row.get('FTTB RİNG NAME', '')),
                lokasyon_id=str(row.get('LOKASYON ID', '')),
                ci_name=str(row.get('CI NAME', '')),
                aciklama=str(row.get('AÇIKLAMA', '')),
                durum=str(row.get('DURUM', ''))
            )
            db.session.add(new_fttb)
            new_count += 1
        
        db.session.commit()
        flash(f'{new_count} yeni kayıt başarıyla eklendi', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'danger')
    
    return redirect(url_for('fttb_optimizasyon'))

@app.route('/export_fttb_optimizasyon_excel')
def export_fttb_optimizasyon_excel():
    fttb_list = FTTBOptimizasyon.query.all()
    
    data = []
    for fttb in fttb_list:
        data.append({
            'YIL': fttb.yil,
            'HAFTA': fttb.hafta,
            'DDO': fttb.ddo,
            'STATÜ': fttb.statu,
            'ÖBEK': fttb.obek,
            'FTTB RİNG NAME': fttb.fttb_ring_name,
            'LOKASYON ID': fttb.lokasyon_id,
            'CI NAME': fttb.ci_name,
            'AÇIKLAMA': fttb.aciklama,
            'DURUM': fttb.durum
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='FTTB Optimizasyon', index=False)
        worksheet = writer.sheets['FTTB Optimizasyon']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'fttb_optimizasyon_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    )

@app.route('/kritik_modernizasyon')
def kritik_modernizasyon():
    total = KritikModernizasyon.query.count()
    return render_template('kritik_modernizasyon.html', total=total)

@app.route('/api/kritik_modernizasyon')
def api_kritik_modernizasyon():
    kritik_list = KritikModernizasyon.query.all()
    return jsonify([{
        'id': k.id,
        'yil': k.yil,
        'hafta': k.hafta,
        'ddo': k.ddo,
        'bultenNo': k.bulten_no,
        'lokasyonId': k.lokasyon_id,
        'isTipi': k.is_tipi,
        'lokasyon': k.lokasyon,
        'aciklama': k.aciklama,
        'durumu': k.durumu
    } for k in kritik_list])

@app.route('/api/kritik_modernizasyon', methods=['POST'])
def api_add_kritik_modernizasyon():
    data = request.get_json()
    
    kritik = KritikModernizasyon(
        yil=data.get('yil'),
        hafta=data.get('hafta'),
        ddo=data.get('ddo'),
        bulten_no=data.get('bultenNo'),
        lokasyon_id=data.get('lokasyonId'),
        is_tipi=data.get('isTipi'),
        lokasyon=data.get('lokasyon'),
        aciklama=data.get('aciklama'),
        durumu=data.get('durumu')
    )
    db.session.add(kritik)
    db.session.commit()
    return jsonify({'status': 'ok'}), 201

@app.route('/api/kritik_modernizasyon/<int:id>', methods=['PUT'])
def api_update_kritik_modernizasyon(id):
    data = request.get_json()
    kritik = KritikModernizasyon.query.get_or_404(id)
    
    kritik.yil = data.get('yil')
    kritik.hafta = data.get('hafta')
    kritik.ddo = data.get('ddo')
    kritik.bulten_no = data.get('bultenNo')
    kritik.lokasyon_id = data.get('lokasyonId')
    kritik.is_tipi = data.get('isTipi')
    kritik.lokasyon = data.get('lokasyon')
    kritik.aciklama = data.get('aciklama')
    kritik.durumu = data.get('durumu')
    kritik.updated_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/kritik_modernizasyon/<int:id>', methods=['DELETE'])
def api_delete_kritik_modernizasyon(id):
    kritik = KritikModernizasyon.query.get_or_404(id)
    db.session.delete(kritik)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/upload_kritik_modernizasyon_excel', methods=['POST'])
def upload_kritik_modernizasyon_excel():
    if 'excel_file' not in request.files:
        flash('Dosya seçilmedi', 'danger')
        return redirect(url_for('kritik_modernizasyon'))
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('Geçersiz dosya', 'danger')
        return redirect(url_for('kritik_modernizasyon'))

    try:
        df = pd.read_excel(file)
        df.columns = [str(col).strip() for col in df.columns]
        
        required_columns = ['YIL', 'HAFTA', 'DDO', 'BÜLTEN NO', 'LOKASYON ID', 
                          'İŞ TİPİ', 'LOKASYON', 'AÇIKLAMA', 'DURUMU']
        
        for col in required_columns:
            if col not in df.columns:
                flash(f"Excel'de '{col}' sütunu eksik!", 'danger')
                return redirect(url_for('kritik_modernizasyon'))
        
        new_count = 0
        for _, row in df.iterrows():
            new_kritik = KritikModernizasyon(
                yil=str(row.get('YIL', '')),
                hafta=str(row.get('HAFTA', '')),
                ddo=str(row.get('DDO', '')),
                bulten_no=str(row.get('BÜLTEN NO', '')),
                lokasyon_id=str(row.get('LOKASYON ID', '')),
                is_tipi=str(row.get('İŞ TİPİ', '')),
                lokasyon=str(row.get('LOKASYON', '')),
                aciklama=str(row.get('AÇIKLAMA', '')),
                durumu=str(row.get('DURUMU', ''))
            )
            db.session.add(new_kritik)
            new_count += 1
        
        db.session.commit()
        flash(f'{new_count} yeni kayıt başarıyla eklendi', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'danger')
    
    return redirect(url_for('kritik_modernizasyon'))

@app.route('/export_kritik_modernizasyon_excel')
def export_kritik_modernizasyon_excel():
    kritik_list = KritikModernizasyon.query.all()
    
    data = []
    for kritik in kritik_list:
        data.append({
            'YIL': kritik.yil,
            'HAFTA': kritik.hafta,
            'DDO': kritik.ddo,
            'BÜLTEN NO': kritik.bulten_no,
            'LOKASYON ID': kritik.lokasyon_id,
            'İŞ TİPİ': kritik.is_tipi,
            'LOKASYON': kritik.lokasyon,
            'AÇIKLAMA': kritik.aciklama,
            'DURUMU': kritik.durumu
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Kritik Modernizasyon', index=False)
        worksheet = writer.sheets['Kritik Modernizasyon']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'kritik_modernizasyon_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    )

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

if __name__ == '__main__':
    app.run(debug=True)