# add_test_data.py
from app import app, db, FiberAriza
from datetime import datetime, timedelta
import random

with app.app_context():
    # Test verileri ekle
    bolgeler = ['Bursa', 'İstanbul', 'Ankara', 'İzmir', 'Antalya']
    nedenler = ['Kablo kopması', 'Ek kutusu arızası', 'Hafriyat', 'Doğal afet']
    
    for i in range(50):  # 50 test kaydı
        ariza = FiberAriza(
            hafta=f"2025-{random.randint(1,10)}",
            bolge=random.choice(bolgeler),
            bulten_no=f"TEST-{1000+i}",
            il=random.choice(bolgeler),
            guzergah=f"Güzergah-{i}",
            lokasyon=f"Lokasyon-{i}",
            ariza_baslangic=datetime.now() - timedelta(days=random.randint(1,30)),
            ariza_bitis=datetime.now() - timedelta(days=random.randint(0,20)),
            ariza_kok_neden=random.choice(nedenler),
            hags_asildi_mi=random.choice(['Evet', 'Hayır']),
            kalici_cozum=random.choice(['Evet', 'Hayır', '']),
            kablo_tipi=random.choice(['ADSS', 'Duct', 'Aerial']),
            aciklama=f"Test arıza kaydı {i}"
        )
        db.session.add(ariza)
    
    db.session.commit()
    print("50 test kaydı eklendi!")
    
    # RAG'i yeniden yükle
    from load_rag_data import load_rag_data
    load_rag_data()