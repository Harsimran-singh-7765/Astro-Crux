import logging
import chromadb
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types
from app.core.config import settings
from functools import lru_cache

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        # 1. Load Search Model
        logger.info("Loading Embedding Model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 2. Connect to Book Database
        self.client = chromadb.PersistentClient(path="chroma_db")
        self.collection = self.client.get_collection("astro_books")
        
        # 3. Connect to Gemini (for HyDE generation)
        self.llm_client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    def _generate_hypothetical_answer(self, query: str) -> str:
        """
        HyDE Step 1: Hallucinate a perfect astrological answer 
        to use as a search query.
        """
        prompt = f"""
        You are an expert Vedic Astrologer.
        User Query: "{query}"
        
        Task: Write a hypothetical paragraph from a classic text (like BPHS) that would answer this. 
        Use technical terms (Houses, Planets, Drishti, Yogas). 
        Do NOT try to be correct about the user's chart. Just write the *theory*.
        """
        
        try:
            response = self.llm_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7, 
                    max_output_tokens=100
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"HyDE Generation failed: {e}")
            return query # Fallback to normal search

    @lru_cache(maxsize=50)
    def get_relevant_context(self, query: str, n_results=3) -> str:
        try:
            # --- HyDE MAGIC STARTS HERE ---
            logger.info(f"Original Query: {query}")
            
            # 1. Generate Hypothetical Document
            hypothetical_doc = self._generate_hypothetical_answer(query)
            logger.info(f"HyDE Generated: {hypothetical_doc[:100]}...")
            
            # 2. Embed the Hypothetical Document (Not the user query!)
            search_vector = self.model.encode([hypothetical_doc]).tolist()
            
            # 3. Search the Real Book Database
            results = self.collection.query(
                query_embeddings=search_vector,
                n_results=n_results
            )
            
            if not results['documents'] or not results['documents'][0]:
                return "No specific Vedic text found."

            # 4. Format Results
            context_parts = []
            for i, doc in enumerate(results['documents'][0]):
                source = results['metadatas'][0][i]['source']
                context_parts.append(f"From {source}:\n{doc}")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"RAG Error: {e}")
            return ""

rag_service = RAGService()