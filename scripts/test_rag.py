# scripts/test_rag.py
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.services.rag_service import rag_service

def test_remedy():
    print("🔮 Testing Acharya's Medicine Cabinet...")
    
    # Question specific to your remedies.txt file
    query = "What is the remedy for a weak Sun or lack of confidence?"
    
    print(f"\n❓ Question: {query}")
    print("... Thinking ...")
    
    context = rag_service.get_relevant_context(query)
    
    print("\n📚 RAG RESULT:")
    print("-" * 50)
    print(context)
    print("-" * 50)

    # Check if it pulled from the correct file
    if "remedies.txt" in context or "Gayatri Mantra" in context:
        print("\n✅ SUCCESS: The system found the CURE!")
    else:
        print("\n⚠️ WARNING: It missed the remedy book.")

if __name__ == "__main__":
    test_remedy()