from fastapi import APIRouter, UploadFile, File, HTTPException
from pdf2image import convert_from_bytes
import pytesseract
import shutil
import os
import uuid

router = APIRouter()

UPLOAD_DIR = "uploads"
TEMP_IMAGE_DIR = "temp_images"
ALLOWED_EXTENSIONS = {".pdf"}  # Types de fichiers autorisés
MAX_FILE_SIZE_MB = 5  # Taille max en Mo

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

def save_uploaded_file(file: UploadFile, directory: str) -> str:
    """Enregistre un fichier dans un répertoire temporaire."""
    file_path = os.path.join(directory, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path

def delete_temp_files(directory: str):
    """Supprime les fichiers temporaires après utilisation."""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier {file_path}: {e}")

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

    file_path = save_uploaded_file(file, UPLOAD_DIR)

    return {"filename": file.filename, "message": "PDF bien reçu", "path": file_path}

@router.post("/analyze-text")
async def analyze_pdf_text(file: UploadFile = File(...)):
    """Analyse un PDF et extrait le texte"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    try:
        pdf_bytes = await file.read()
        images = convert_from_bytes(pdf_bytes)

        extracted_text = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img)
            extracted_text.append({"page": i + 1, "text": text})

        delete_temp_files(TEMP_IMAGE_DIR)

        return {"status": "Analyse réussie", "text_data": extracted_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du PDF : {str(e)}")

@router.post("/analyze-images")
async def analyze_pdf_images(file: UploadFile = File(...)):
    """Convertit un PDF en images et retourne les chemins des images générées."""
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    try:
        pdf_bytes = await file.read()
        images = convert_from_bytes(pdf_bytes)

        image_paths = []
        for i, img in enumerate(images):
            image_filename = f"{TEMP_IMAGE_DIR}/page_{uuid.uuid4().hex}.png"
            img.save(image_filename, "PNG")
            image_paths.append(image_filename)

        return {"status": "Conversion réussie", "images": image_paths}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du PDF : {str(e)}")
