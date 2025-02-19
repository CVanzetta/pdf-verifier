from fastapi import APIRouter, UploadFile, File, HTTPException
from pdf2image import convert_from_bytes
import pytesseract
import shutil
import os
import uuid
import cv2  # OpenCV pour le prétraitement
import numpy as np

router = APIRouter()

UPLOAD_DIR = "uploads"
TEMP_IMAGE_DIR = "temp_images"
ALLOWED_EXTENSIONS = {".pdf"}  # Types de fichiers autorisés
MAX_FILE_SIZE_MB = 5  # Taille max en Mo

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

def preprocess_image(image):
    """
    Applique un prétraitement à une image pour améliorer la reconnaissance OCR.
    - Convertit en niveaux de gris
    - Applique un flou gaussien
    - Effectue une binarisation avec Otsu
    """
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

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

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename, "message": "PDF bien reçu"}

@router.post("/analyze-text")
async def analyze_pdf(file: UploadFile = File(...)):
    """Analyse un PDF, applique un prétraitement et extrait le texte OCR"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    try:
        # Lire le contenu du fichier PDF
        pdf_bytes = await file.read()
        
        # Convertir le PDF en images
        images = convert_from_bytes(pdf_bytes)

        extracted_text = []
        for i, img in enumerate(images):
            processed_img = preprocess_image(img)  # 🔹 OpenCV prétraitement ici
            text = pytesseract.image_to_string(processed_img)
            extracted_text.append({"page": i + 1, "text": text})

        return {"status": "Analyse réussie", "text_data": extracted_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du PDF : {str(e)}")

@router.post("/analyze-images")
async def analyze_pdf_images(file: UploadFile = File(...)):
    """Convertit un PDF en images et applique un prétraitement OpenCV"""
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
    
    try:
        pdf_bytes = await file.read()
        images = convert_from_bytes(pdf_bytes)

        image_paths = []
        for i, img in enumerate(images):
            processed_img = preprocess_image(img)  # 🔹 OpenCV prétraitement ici
            image_filename = f"{TEMP_IMAGE_DIR}/page_{uuid.uuid4().hex}.png"
            cv2.imwrite(image_filename, processed_img)  # Sauvegarde l'image traitée
            image_paths.append(image_filename)

        return {"status": "Conversion réussie", "images": image_paths}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du PDF : {str(e)}")
