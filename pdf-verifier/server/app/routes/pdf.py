from fastapi import APIRouter, UploadFile, File, HTTPException
from pdf2image import convert_from_bytes
import pytesseract
import shutil
import os
from werkzeug.utils import secure_filename
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Mets le bon chemin si différent


router = APIRouter()

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".pdf"}  # Types de fichiers autorisés
MAX_FILE_SIZE_MB = 5  # Taille max en Mo

# Vérification de l'installation de Tesseract
try:
    pytesseract.get_tesseract_version()
except Exception:
    raise RuntimeError("Tesseract OCR n'est pas installé ou mal configuré. Vérifiez son installation.")

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Enregistre un fichier PDF reçu avec vérifications d'extension et de taille"""
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    # Vérifier l'extension
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont autorisés")

    # Lire le contenu du fichier pour vérifier la taille
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Le fichier dépasse la limite de {MAX_FILE_SIZE_MB} Mo")
    
    # Réinitialiser le pointeur de lecture du fichier
    await file.seek(0)

    # Sécuriser le nom du fichier
    safe_filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": safe_filename, "message": "PDF bien reçu, stocké temporairement"}

@router.post("/analyze")
async def analyze_pdf(file: UploadFile = File(...)):
    """Analyse un PDF, extrait le texte et supprime le fichier après utilisation"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    try:
        # Lire le contenu du fichier PDF
        pdf_bytes = await file.read()
        
        # Convertir le PDF en images
        images = convert_from_bytes(pdf_bytes)

        extracted_text = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img)
            extracted_text.append({"page": i + 1, "text": text})

        # Supprimer le fichier temporaire après analyse
        file_path = os.path.join(UPLOAD_DIR, secure_filename(file.filename))
        if os.path.exists(file_path):
            os.remove(file_path)

        return {"status": "Analyse réussie", "text_data": extracted_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du PDF : {str(e)}")
