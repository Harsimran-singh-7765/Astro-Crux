import logging
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.api_router import api_router

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Astro-Crux API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# --- Auto-create and mount static directories ---

def setup_directory(dir_name: str, description: str = "files"):
    """
    Create directory if it doesn't exist and return the path.
    
    Args:
        dir_name: Name of the directory to create
        description: Description for logging purposes
    
    Returns:
        Path object of the directory
    """
    # Get the directory where main.py is located
    base_dir = Path(__file__).resolve().parent.parent
    target_dir = base_dir / dir_name
    
    if not target_dir.exists():
        logger.warning(f"Directory '{dir_name}' not found. Creating it now...")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a README file to explain the directory
        readme = target_dir / "README.md"
        readme.write_text(f"# {dir_name.capitalize()} Directory\n\nPlace your {description} here.")
        
        logger.info(f"✓ Created '{dir_name}' directory at: {target_dir}")
    else:
        logger.info(f"✓ Found existing '{dir_name}' directory at: {target_dir}")
    
    return target_dir

# Setup static directories
try:
    static_path = setup_directory("static", "CSS, JS, images, and other static assets")
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info("✓ Mounted /static endpoint")
except Exception as e:
    logger.error(f"Failed to mount /static: {e}")

try:
    testing_path = setup_directory("testing", "testing files and resources")
    app.mount("/testing", StaticFiles(directory=str(testing_path)), name="testing")
    logger.info("✓ Mounted /testing endpoint")
except Exception as e:
    logger.error(f"Failed to mount /testing: {e}")

# --- Root Endpoints ---

@app.get("/")
def root():
    return {"message": "Astro-Crux Engine is Online. Stars are aligned."}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Astro-Crux API",
        "endpoints": {
            "api": "/api/v1",
            "docs": "/docs",
            "static": "/static",
            "testing": "/testing"
        }
    }

# Optional: Startup event to log server info
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("🌟 Astro-Crux API Server Starting...")
    logger.info("=" * 60)
    logger.info(f"📍 API Base: /api/v1")
    logger.info(f"📚 Docs: /docs")
    logger.info(f"🎨 Static Files: /static")
    logger.info(f"🧪 Testing Files: /testing")
    logger.info("=" * 60)