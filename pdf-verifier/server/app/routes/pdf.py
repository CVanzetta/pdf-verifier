from fastapi import APIRouter, UploadFile, File, HTTPException
from pdf2image import convert_from_bytes
import pytesseract
import shutil
import os
import uuid
import cv2  # OpenCV pour le prétraitement et la détection
import numpy as np
import fitz  # PyMuPDF pour extraire les images
import logging

router = APIRouter()

# Dossiers de stockage
UPLOAD_DIR = "uploads"
TEMP_IMAGE_DIR = "temp_images"
EXTRACTED_IMAGES_DIR = "extracted_images"
REFERENCE_MODELS_DIR = "reference_models"
ALLOWED_EXTENSIONS = {".pdf"}  # Types de fichiers autorisés
MAX_FILE_SIZE_MB = 5  # Taille max en Mo
CONFIDENCE_THRESHOLD = 10  # Score minimum pour une correspondance valide

# Création des dossiers
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)
os.makedirs(EXTRACTED_IMAGES_DIR, exist_ok=True)
os.makedirs(REFERENCE_MODELS_DIR, exist_ok=True)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preprocess_image(image):
    """Prétraitement OpenCV : conversion en niveaux de gris et binarisation."""
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def load_reference_images():
    """Charge les modèles d’images de référence (logos, signatures, filigranes)."""
    models = {}
    for model_name in os.listdir(REFERENCE_MODELS_DIR):
        model_path = os.path.join(REFERENCE_MODELS_DIR, model_name)
        models[model_name] = cv2.imread(model_path, cv2.IMREAD_GRAYSCALE)
    return models

def match_images(extracted_image, reference_images, method="ORB"):
    """Compare une image extraite avec les modèles et retourne la meilleure correspondance."""
    if method not in ["ORB", "SIFT"]:
        raise ValueError("Méthode non valide. Utiliser 'ORB' ou 'SIFT'.")

    detector = cv2.ORB_create() if method == "ORB" else cv2.SIFT_create()
    kp1, des1 = detector.detectAndCompute(extracted_image, None)

    best_match = None
    best_score = 0

    for model_name, model_img in reference_images.items():
        kp2, des2 = detector.detectAndCompute(model_img, None)

        if des1 is not None and des2 is not None:
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)
            score = len(matches)

            if score > best_score:
                best_score = score
                best_match = model_name

    return best_match, best_score

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Enregistre un fichier PDF après vérifications d'extension et de taille."""
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont autorisés")

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Le fichier dépasse la limite de {MAX_FILE_SIZE_MB} Mo")

    await file.seek(0)

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logger.info(f"Fichier reçu : {file.filename}")
    return {"filename": file.filename, "message": "PDF bien reçu"}

@router.post("/extract-images")
async def extract_images_from_pdf(file: UploadFile = File(...)):
    """Extrait les images intégrées au PDF (logos, signatures, filigranes)."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    try:
        pdf_bytes = await file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        image_paths = []
        for page_number, page in enumerate(pdf_document):
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]

                image_filename = f"{EXTRACTED_IMAGES_DIR}/page_{page_number+1}_img_{img_index}.png"

                with open(image_filename, "wb") as image_file:
                    image_file.write(image_bytes)

                image_paths.append(image_filename)

        return {"status": "Extraction réussie", "images": image_paths}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'extraction des images du PDF : {str(e)}")

@router.post("/detect-elements")
async def detect_elements_in_pdf(file: UploadFile = File(...), method: str = "ORB"):
    """Compare les images extraites du PDF aux modèles de référence avec ORB/SIFT."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    try:
        pdf_bytes = await file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        detection_results = []
        reference_images = load_reference_images()

        for page_number, page in enumerate(pdf_document):
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]

                image_array = np.frombuffer(image_bytes, dtype=np.uint8)
                extracted_image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)

                best_match, best_score = match_images(extracted_image, reference_images, method)

                detection_results.append({
                    "page": page_number + 1,
                    "image_index": img_index,
                    "best_match": best_match if best_match and best_score > CONFIDENCE_THRESHOLD else "Aucune correspondance",
                    "score": best_score
                })

        return {"status": "Détection terminée", "results": detection_results}

    except Exception as e:
        return HTTPException(status_code=500, detail=f"Erreur lors de la détection des éléments : {str(e)}")
