from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import documents, projections

app = FastAPI(
    title="PymeScope API",
    description="Backend para análisis financiero de PYMEs",
    version="1.0.0"
)

origins = [
    "http://localhost:5173", # Tu Frontend local
    "http://127.0.0.1:5173",
    "pyme-scope-tt.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permitir GET, POST, DELETE, etc.
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api", tags=["Documentos"])
app.include_router(projections.router, prefix="/api", tags=["Proyecciones"])

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "PymeScope Backend"}
