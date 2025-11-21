from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Astro-Crux"
    
    # API Keys (Loaded from .env)
    GOOGLE_API_KEY: str
    DEEPGRAM_API_KEY: str
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_INITDB_DATABASE: str = "astro_hack_db"

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()