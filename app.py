import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd

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
        
        return render_template('explorer.html', 
                            items=items,
                            current_path=subpath,
                            breadcrumbs=breadcrumbs,
                            parent_dir=parent_dir)
    
    except Exception as e:
        flash(f"Hata oluştu: {str(e)}", "error")
        return redirect(url_for('browse'))

@app.route('/upload', methods=['POST'])
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



@app.route('/upload', methods=['POST'])
def upload_excel():
    if 'excel_file' not in request.files:
        flash('Dosya seçilmedi', 'danger')
        return redirect(url_for('index'))
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('Geçersiz dosya', 'danger')
        return redirect(url_for('index'))
    
    try:
        df = pd.read_excel(file)
        existing_nos = {x.bulten_no for x in FiberAriza.query.all()}
        
        new_count = 0
        for _, row in df.iterrows():
            bulten_no = str(row['Bülten Numarası'])
            if bulten_no not in existing_nos:
                new_ariza = FiberAriza(
                    hafta=row['Hafta'],
                    bolge=row['Bölge'],
                    bulten_no=bulten_no,
                    il=row['İL'],
                    guzergah=row['Güzergah'],
                    lokasyon=row['Lokasyon'],
                    ariza_baslangic=datetime.strptime(row['Arıza Başlangıç'], '%d %B %Y %H:%M:%S'),
                    ariza_bitis=datetime.strptime(row['Arıza Bitiş'], '%d %B %Y %H:%M:%S'),
                    ariza_konsolide=row['Arıza Konsolide Kök Neden'],
                    ariza_kok_neden=row['Arıza Kök Neden'],
                    hags_asildi_mi=row['HAGS Aşıldı mı'],
                    refakat_durumu=row['Refakat Durumu'],
                    serivs_etkisi=row['SERİVS ETKİSİ'],      # H sütunu
                    servis_etkisi=row['Servis Etkisi'],      # S sütunu
                    ariza_suresi=row['Arıza Süresi'],
                    # Yeni alanlar
                    kordinat_a=row.get('KORDINAT A', ''),
                    kordinat_b=row.get('KORDINAT B', ''),
                    kablo_tipi=row.get('KABLO TIPI', ''),
                    hags_suresi=row.get('HAGS SURESI', ''),
                    kesinti_suresi=row.get('KESINTI SÜRESİ', ''),
                    kalici_cozum=row.get('KALICI ÇÖZÜM SAĞLANDI', ''),
                    kullanilan_malzeme=row.get('KULLANILAN MALZEME', ''),
                    aciklama=row.get('ACIKLAMA', '')
                )
                db.session.add(new_ariza)
                new_count += 1
        
        db.session.commit()
        flash(f'{new_count} yeni kayıt başarıyla eklendi', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))


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

if __name__ == '__main__':
    app.run(debug=True)