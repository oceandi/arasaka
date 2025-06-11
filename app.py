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

@app.route('/')
def home():
    return redirect(url_for('browse'))

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
    if FiberAriza.query.filter_by(bulten_no=data.get('bultenNo')).first():
        return jsonify({'error': 'Bu Bülten Numarası ile zaten kayıt var!'}), 400

    ariza = FiberAriza(
        hafta=data.get('hafta'),
        bolge=data.get('bolge'),
        bulten_no=data.get('bultenNo'),
        il=data.get('il'),
        guzergah=data.get('guzergah'),
        kordinat_a=data.get('kordinatA'),
        kordinat_b=data.get('kordinatB'),
        ariza_baslangic=datetime.fromisoformat(data.get('baslangicTarihi')) if data.get('baslangicTarihi') else None,
        ariza_bitis=datetime.fromisoformat(data.get('bitisTarihi')) if data.get('bitisTarihi') else None,
        kablo_tipi=data.get('kabloTipi'),
        ariza_kok_neden=data.get('kokNeden'),
        hags_asildi_mi=data.get('hags'),
        servis_etkisi=data.get('servisEtkisi'),
        ariza_suresi=data.get('arizaSuresi'),
        kalici_cozum=data.get('kaliciCozum'),
        ariza_konsolide=data.get('arizaKonsolide'),
        lokasyon=data.get('lokasyon'),
        refakat_durumu=data.get('refakatDurumu'),
        hags_suresi=data.get('hagsSuresi'),
        kesinti_suresi=data.get('kesintiSuresi'),
        kullanilan_malzeme=data.get('kullanilanMalzeme'),
        aciklama=data.get('aciklama'),
        serivs_etkisi=data.get('serivsEtkisi')
    )
    db.session.add(ariza)
    db.session.commit()
    return jsonify({'status': 'ok'}), 201

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
    """Harita için arıza verilerini döndür"""
    arizalar = FiberAriza.query.filter(
        FiberAriza.kordinat_a != '',
        FiberAriza.kordinat_b != ''
    ).all()
    
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

if __name__ == '__main__':
    app.run(debug=True)