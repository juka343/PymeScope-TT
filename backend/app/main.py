from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import documents

app = FastAPI(
    title="PymeScope API",
    description="Backend para análisis financiero de PYMEs",
    version="1.0.0"
)

origins = [
    "http://localhost:5174", # Tu Frontend local
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permitir GET, POST, DELETE, etc.
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api", tags=["Documentos"])

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "PymeScope Backend"}
