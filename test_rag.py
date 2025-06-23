# test_rag.py
from advanced_rag import AdvancedFiberRAG

rag = AdvancedFiberRAG()

# Test soruları
test_queries = [
    "HAGS aşan arızalar hangileri?",
    "Bursa'da kaç arıza var?",
    "Kablo kopması nedeniyle oluşan arızalar",
    "Çözülmemiş arızaların listesi"
]

for query in test_queries:
    print(f"\n🔍 Soru: {query}")
    context = rag.get_intelligent_context(query)
    print(context[:500] + "...")