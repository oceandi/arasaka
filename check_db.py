# check_db.py
from app import app, db, FiberAriza

with app.app_context():
    count = FiberAriza.query.count()
    print(f"Veritabanında toplam {count} arıza kaydı var")
    
    # İlk 5 kaydı göster
    arizalar = FiberAriza.query.limit(5).all()
    for ariza in arizalar:
        print(f"- {ariza.bulten_no}: {ariza.bolge} - {ariza.il}")