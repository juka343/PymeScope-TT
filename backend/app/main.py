from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import documents, projections

app = FastAPI(
    title="PymeScope API",
    description="Backend para análisis financiero de PYMEs",
    version="1.0.0"
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://pyme-scope-tt.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Para Vercel Services: /api se usa como routePrefix y probablemente se remueve antes de llegar a FastAPI
app.include_router(documents.router, tags=["Documentos"])
app.include_router(projections.router, tags=["Proyecciones"])

# Para local: mantiene compatibilidad con http://localhost:8000/api/...
app.include_router(documents.router, prefix="/api", tags=["Documentos Local"])
app.include_router(projections.router, prefix="/api", tags=["Proyecciones Local"])

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "PymeScope Backend"}

@app.get("/api/health")
def health_check_api():
    return {"status": "ok", "system": "PymeScope Backend"}