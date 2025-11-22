import os
import chromadb
from sentence_transformers import SentenceTransformer

# Config
DATA_DIR = "data/books"
DB_DIR = "chroma_db" 

def simple_text_splitter(text, chunk_size=600, chunk_overlap=100):
    """
    A simple function to split text into chunks without needing LangChain.
    Splits by periods/newlines to keep sentences intact.
    """
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        
        # If we are at the end, just take the rest
        if end >= text_len:
            chunks.append(text[start:])
            break
        
        # Find the last period or newline before the cutoff to avoid cutting words
        # Look in the last 20% of the chunk for a break point
        lookback = int(chunk_size * 0.2)
        break_point = -1
        
        # Try finding a period
        last_period = text.rfind('.', start, end)
        if last_period > (end - lookback):
            break_point = last_period + 1
        else:
            # Try finding a newline
            last_newline = text.rfind('\n', start, end)
            if last_newline > (end - lookback):
                break_point = last_newline + 1
        
        if break_point != -1:
            chunks.append(text[start:break_point].strip())
            start = break_point - chunk_overlap # Overlap for context
        else:
            # Hard cut if no punctuation found
            chunks.append(text[start:end].strip())
            start = end - chunk_overlap

    return [c for c in chunks if len(c) > 50] # Filter empty chunks

def ingest_books():
    print("DEBUG: Script has started...")
    print("📚 Starting Vedic Library Ingestion (Zero-Dependency Mode)...")
    
    # 1. Setup
    model = SentenceTransformer('all-MiniLM-L6-v2')
    # Save to disk folder 'chroma_db'
    client = chromadb.PersistentClient(path=DB_DIR)
    
    # Delete old collection to start fresh
    try:
        client.delete_collection("astro_books")
    except:
        pass
        
    collection = client.create_collection("astro_books")
    
    # 2. Process Books
    documents = []
    metadatas = []
    ids = []
    id_counter = 0

    if not os.path.exists(DATA_DIR):
        print(f"❌ Error: {DATA_DIR} folder nahi mila!")
        return

    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".txt")]
    if not files:
        print(f"❌ Error: {DATA_DIR} mein koi .txt file nahi hai!")
        return

    for filename in files:
        path = os.path.join(DATA_DIR, filename)
        print(f"📖 Reading: {filename}...")
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            
        # Use our custom splitter instead of LangChain
        chunks = simple_text_splitter(text)
        print(f"   -> Found {len(chunks)} chunks.")
        
        for chunk in chunks:
            documents.append(chunk)
            metadatas.append({"source": filename})
            ids.append(f"doc_{id_counter}")
            id_counter += 1

    # 3. Batch Insert
    if documents:
        print(f"🧠 Embedding {len(documents)} verses... (This might take a minute)")
        batch_size = 200
        for i in range(0, len(documents), batch_size):
            end = min(i + batch_size, len(documents))
            collection.add(
                documents=documents[i:end],
                embeddings=model.encode(documents[i:end]).tolist(),
                metadatas=metadatas[i:end],
                ids=ids[i:end]
            )
            print(f"   Processed {end}/{len(documents)}")
            
        print(f"✅ Library Ready! Database saved at: {os.path.abspath(DB_DIR)}")
    else:
        print("⚠️ No valid text found to ingest.")

if __name__ == "__main__":
    ingest_books()