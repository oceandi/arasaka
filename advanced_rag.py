from rag_setup import FiberArizaRAG
from sqlalchemy import func
from app import app, db, FiberAriza

class AdvancedFiberRAG(FiberArizaRAG):
    def create_specialized_indices(self):
        """Özel indeksler oluştur"""
        with app.app_context():
            # HAGS aşan arızalar için özel collection
            hags_collection = self.client.get_or_create_collection(
                name="hags_violations",
                embedding_function=self.embedding_fn
            )
            
            # Çözülmemiş arızalar için
            unsolved_collection = self.client.get_or_create_collection(
                name="unsolved_issues",
                embedding_function=self.embedding_fn
            )
            
            # Bölgesel analiz için
            regional_collection = self.client.get_or_create_collection(
                name="regional_analysis",
                embedding_function=self.embedding_fn
            )
    
    def semantic_search_with_filters(self, query, filters=None):
        """Filtreli semantik arama"""
        where_clause = {}
        
        if filters:
            if 'bolge' in filters:
                where_clause['bolge'] = filters['bolge']
            if 'hags_asildi' in filters:
                where_clause['hags_asildi'] = filters['hags_asildi']
            if 'cozuldu' in filters:
                where_clause['cozuldu'] = filters['cozuldu']
        
        results = self.collection.query(
            query_texts=[query],
            n_results=10,
            where=where_clause if where_clause else None
        )
        
        return results
    
    def get_intelligent_context(self, query):
        """Akıllı context oluştur"""
        # Normal arama
        general_results = self.search(query, n_results=3)
        
        # HAGS anahtar kelimesi varsa
        if 'hags' in query.lower():
            hags_results = self.semantic_search_with_filters(
                query, 
                filters={'hags_asildi': 'Evet'}
            )
            
        # Bölge ismi geçiyorsa
        with app.app_context():
            bolgeler = db.session.query(FiberAriza.bolge).distinct().all()
            for bolge in bolgeler:
                if bolge[0] and bolge[0].lower() in query.lower():
                    regional_results = self.semantic_search_with_filters(
                        query,
                        filters={'bolge': bolge[0]}
                    )
        
        # Context'i birleştir
        context = self._build_rich_context(general_results, query)
        return context
    
    def _build_rich_context(self, results, query):
        """Zengin context oluştur"""
        context = f"Kullanıcı sorusu: '{query}' ile ilgili bilgiler:\n\n"
        
        # En alakalı kayıtlar
        context += "📊 İlgili Arıza Kayıtları:\n"
        for i, doc in enumerate(results['documents'][0][:5]):
            context += f"\nKayıt {i+1}:\n{doc}\n"
        
        # İstatistikler
        with app.app_context():
            if 'hags' in query.lower():
                hags_stats = db.session.query(
                    FiberAriza.bolge,
                    func.count(FiberAriza.id)
                ).filter(
                    FiberAriza.hags_asildi_mi == 'Evet'
                ).group_by(FiberAriza.bolge).all()
                
                context += "\n📈 HAGS İstatistikleri:\n"
                for bolge, count in hags_stats[:5]:
                    context += f"- {bolge}: {count} adet HAGS aşımı\n"
        
        return context