import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException

# Exemples de constantes (à adapter à ta config existante)
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE_MB = 5
UPLOAD_DIR = "uploads"

router = APIRouter()

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Enregistre le PDF après vérification de l'extension et de la taille."""
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont autorisés")

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Le fichier dépasse la limite de {MAX_FILE_SIZE_MB} Mo")

    # Repositionner le curseur au début (utile si on relit le fichier)
    await file.seek(0)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename, "message": "PDF bien reçu"}
