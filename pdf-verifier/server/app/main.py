from fastapi import FastAPI
from app.routes import pdf

app = FastAPI(title="PDF Verification API")

# Inclure les routes
app.include_router(pdf.router, prefix="/pdf", tags=["PDF"])

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de vérification de PDF"}
