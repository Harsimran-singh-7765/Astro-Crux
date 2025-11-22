# scripts/test_rag.py
import sys
import os

# Add the project root to python path so we can import app modules
sys.path.append(os.getcwd())

from app.services.rag_service import rag_service

def test_brain():
    print("🔮 Testing Acharya's Knowledge from BPHS...")
    
    # 1. Ask a specific question covered in BPHS
    query = "What happens if Sun is in the 1st House?"
    
    print(f"\n❓ Question: {query}")
    print("... Thinking (Generating HyDE + Searching Vector DB) ...")
    
    # 2. Get Context
    context = rag_service.get_relevant_context(query)
    
    print("\n📚 RAG RESULT:")
    print("-" * 50)
    print(context)
    print("-" * 50)

    if "BPHS" in context or "Brihat" in context or "bphs.txt" in context:
        print("\n✅ SUCCESS: The system is reading from the book!")
    else:
        print("\n⚠️ WARNING: Did not see 'BPHS' in source. Check if ingestion worked.")

if __name__ == "__main__":
    test_brain()