from fastapi import APIRouter, UploadFile, File, HTTPException
from pdf2image import convert_from_bytes
import pytesseract
import shutil
import os
import uuid
import cv2  # OpenCV pour le prétraitement
import numpy as np
import fitz  # PyMuPDF pour extraire les images
import logging

router = APIRouter()

# Dossiers de stockage
UPLOAD_DIR = "uploads"
TEMP_IMAGE_DIR = "temp_images"
EXTRACTED_IMAGES_DIR = "extracted_images"
ALLOWED_EXTENSIONS = {".pdf"}  # Types de fichiers autorisés
MAX_FILE_SIZE_MB = 5  # Taille max en Mo

# Création des dossiers
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)
os.makedirs(EXTRACTED_IMAGES_DIR, exist_ok=True)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preprocess_image(image):
    """Prétraitement OpenCV : conversion en niveaux de gris et binarisation."""
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

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

@router.post("/analyze-text")
async def analyze_pdf(file: UploadFile = File(...)):
    """Analyse un PDF, applique un prétraitement et extrait le texte OCR."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    try:
        pdf_bytes = await file.read()
        images = convert_from_bytes(pdf_bytes)

        extracted_text = []
        for i, img in enumerate(images):
            processed_img = preprocess_image(img)  
            text = pytesseract.image_to_string(processed_img)
            extracted_text.append({"page": i + 1, "text": text})

        return {"status": "Analyse réussie", "text_data": extracted_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du PDF : {str(e)}")

@router.post("/convert-images")
async def convert_pdf_to_images(file: UploadFile = File(...)):
    """Convertit un PDF en images avec prétraitement OpenCV."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
    
    try:
        pdf_bytes = await file.read()
        images = convert_from_bytes(pdf_bytes)

        image_paths = []
        for i, img in enumerate(images):
            processed_img = preprocess_image(img)
            image_filename = f"{TEMP_IMAGE_DIR}/page_{uuid.uuid4().hex}.png"
            cv2.imwrite(image_filename, processed_img)  
            image_paths.append(image_filename)

        return {"status": "Conversion réussie", "images": image_paths}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du PDF : {str(e)}")

@router.post("/extract-images")
async def extract_images_from_pdf(file: UploadFile = File(...)):
    """Extrait les images intégrées au PDF (logos, signatures, etc.)."""
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

                # Générer un nom de fichier unique
                image_filename = f"{EXTRACTED_IMAGES_DIR}/page_{page_number+1}_img_{img_index}.png"

                # Sauvegarder l'image extraite
                with open(image_filename, "wb") as image_file:
                    image_file.write(image_bytes)
                
                image_paths.append(image_filename)

        logger.info(f"Extraction d'images terminée pour {file.filename}")

        # TODO : Comparer ces images aux modèles connus (logos, signatures, filigranes)
        # Étapes :
        # 1️⃣ Charger les modèles d’images de référence
        # 2️⃣ Appliquer ORB/SIFT pour comparer chaque image extraite avec les modèles
        # 3️⃣ Retourner un score de correspondance (présent/absent + taux de confiance)

        return {"status": "Extraction réussie", "images": image_paths}

    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des images du PDF : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'extraction des images du PDF : {str(e)}")
    
@router.post("/detect-elements")
async def detect_elements_in_pdf(file: UploadFile = File(...)):
    """Compare les images extraites du PDF aux modèles de référence avec ORB"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    try:
        # Lire le contenu du fichier PDF
        pdf_bytes = await file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Liste pour stocker les résultats
        detection_results = []

        # Charger les modèles de référence (logos, signatures, filigranes)
        model_images = {}
        model_dir = "reference_models"  # 📌 Dossier où stocker les modèles
        for model_name in os.listdir(model_dir):
            model_path = os.path.join(model_dir, model_name)
            model_images[model_name] = cv2.imread(model_path, cv2.IMREAD_GRAYSCALE)

        # Initialiser ORB
        orb = cv2.ORB_create()

        for page_number, page in enumerate(pdf_document):
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]

                # Convertir l'image en format lisible par OpenCV
                image_array = np.frombuffer(image_bytes, dtype=np.uint8)
                extracted_image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)

                # Calculer les descripteurs ORB pour l'image extraite
                kp1, des1 = orb.detectAndCompute(extracted_image, None)

                best_match = None
                best_score = 0

                for model_name, model_img in model_images.items():
                    kp2, des2 = orb.detectAndCompute(model_img, None)

                    # Vérifier que descripteurs existent
                    if des1 is not None and des2 is not None:
                        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                        matches = bf.match(des1, des2)

                        # Calculer un score de correspondance basé sur le nombre de bons matchs
                        score = len(matches)
                        if score > best_score:
                            best_score = score
                            best_match = model_name

                detection_results.append({
                    "page": page_number + 1,
                    "image_index": img_index,
                    "best_match": best_match if best_match else "Aucune correspondance",
                    "score": best_score
                })

        logger.info(f"Détection d'éléments terminée pour {file.filename}")
        return {"status": "Détection terminée", "results": detection_results}

    except Exception as e:
        logger.error(f"Erreur lors de la détection des éléments : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la détection des éléments : {str(e)}")
