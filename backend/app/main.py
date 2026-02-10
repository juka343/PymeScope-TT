from fastapi import FastAPI
#from app.api.routes import documents_router

app = FastAPI(
    title="PymeScope API",
    description="Backend para análisis financiero de PYMEs",
    version="1.0.0"
)

#app.include_router(documents_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
