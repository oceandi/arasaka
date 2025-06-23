from app import app, db, FiberAriza
from rag_setup import FiberArizaRAG

def load_rag_data():
    """RAG'e veri yükle"""
    rag = FiberArizaRAG()
    
    with app.app_context():
        arizalar = FiberAriza.query.all()
        rag.load_data_from_db(arizalar)
        print(f"Toplam {len(arizalar)} arıza RAG'e yüklendi!")

if __name__ == "__main__":
    load_rag_data()