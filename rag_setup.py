import chromadb
from chromadb.utils import embedding_functions
import json
import os

class FiberArizaRAG:
    def __init__(self):
        # ChromaDB client
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # Türkçe destekli embedding
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        # Collection oluştur
        self.collection = self.client.get_or_create_collection(
            name="fiber_ariza",
            embedding_function=self.embedding_fn
        )
    
    def load_data_from_db(self, arizalar):
        """Arıza listesini vector DB'ye yükle"""
        documents = []
        metadatas = []
        ids = []
        
        for ariza in arizalar:
            # Her arızayı metin olarak hazırla
            doc = f"""
            Bülten No: {ariza.bulten_no}
            Bölge: {ariza.bolge}
            İl: {ariza.il}
            Güzergah: {ariza.guzergah}
            Lokasyon: {ariza.lokasyon}
            Arıza Kök Nedeni: {ariza.ariza_kok_neden}
            HAGS Aşıldı mı: {ariza.hags_asildi_mi}
            Kalıcı Çözüm: {ariza.kalici_cozum}
            Kablo Tipi: {ariza.kablo_tipi}
            Açıklama: {ariza.aciklama}
            """
            
            documents.append(doc)
            metadatas.append({
                "id": ariza.id,
                "bulten_no": ariza.bulten_no,
                "bolge": ariza.bolge,
                "il": ariza.il,
                "hags_asildi": ariza.hags_asildi_mi,
                "cozuldu": ariza.kalici_cozum
            })
            ids.append(f"ariza_{ariza.id}")
        
        # ChromaDB'ye ekle
        if documents:  # Boş değilse ekle
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
        print(f"✅ {len(documents)} arıza kaydı vector DB'ye yüklendi!")
    
    def search(self, query, n_results=5):
        """Benzer arızaları bul"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
    
    def get_context_for_llm(self, query):
        """LLM için context hazırla"""
        results = self.search(query)
        
        if not results['documents'] or not results['documents'][0]:
            return "İlgili arıza kaydı bulunamadı."
        
        context = "İlgili arıza kayıtları:\n\n"
        
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            context += f"Kayıt {i+1}:\n{doc}\n"
            context += f"Bölge: {metadata.get('bolge')}, Çözüldü: {metadata.get('cozuldu')}\n\n"
        
        return context