from fastapi import FastAPI
from app.routes import pdf  # Assure-toi que le chemin est correct

app = FastAPI(
    title="PDF Verification API",
    description="API pour l'analyse et la vérification des PDF",
    version="1.1.0"
)

# Ajouter les routes du fichier `pdf.py`
app.include_router(pdf.router, prefix="/pdf")

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de vérification de PDF"}