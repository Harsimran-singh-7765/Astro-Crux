import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.api_router import api_router

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

app = FastAPI(title="Astro-Crux API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/testing", StaticFiles(directory="testing"), name="testing")

@app.get("/")
def root():
    return {"message": "Astro-Crux Engine is Online. Stars are aligned."}
