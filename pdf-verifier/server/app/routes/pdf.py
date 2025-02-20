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

@router.post("/convert-images")
async def convert_pdf_to_images(file: UploadFile = File(...)):
    """Convertit un PDF en images avec prétraitement OpenCV (préparation OCR)."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
    
    try:
        pdf_bytes = await file.read()
        images = convert_from_bytes(pdf_bytes)

        image_paths = []
        for i, img in enumerate(images):
            processed_img = preprocess_image(img)
            image_filename = f"{TEMP_IMAGE_DIR}/page_{i+1}_{uuid.uuid4().hex}.png"
            cv2.imwrite(image_filename, processed_img)  
            image_paths.append(image_filename)

        return {"status": "Conversion réussie", "images": image_paths}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la conversion : {str(e)}")

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
        return HTTPException(status_code=500, detail=f"Erreur OCR : {str(e)}")

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
        return HTTPException(status_code=500, detail=f"Erreur extraction images : {str(e)}")

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

        # Vérifier qu'on a bien chargé des modèles de référence
        if not reference_images:
            raise HTTPException(status_code=500, detail="Aucun modèle d'image de référence trouvé !")

        for page_number, page in enumerate(pdf_document):
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)

                if not base_image:
                    logger.warning(f"Impossible d'extraire l'image {img_index} de la page {page_number + 1}")
                    continue

                image_bytes = base_image["image"]

                # Convertir l'image en format utilisable par OpenCV
                image_array = np.frombuffer(image_bytes, dtype=np.uint8)
                extracted_image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)

                # Vérifier si l'image a bien été décodée
                if extracted_image is None:
                    logger.warning(f"L'image {img_index} de la page {page_number + 1} n'a pas pu être chargée.")
                    continue

                best_match, best_score = match_images(extracted_image, reference_images, method)

                # Déterminer le seuil de validation en fonction du type d'élément détecté 450-500 Seuil élevé et 300-450 Seuil moyen moins de 300 Seuil bas (rique de faux positifs)
                if best_match:
                    if "filigrane" in best_match.lower():
                        threshold = 450
                    elif "logo" in best_match.lower():
                        threshold = 450
                    elif "signature" in best_match.lower():
                        threshold = 300
                    else:
                        threshold = CONFIDENCE_THRESHOLD  # Seuil par défaut

                    # Vérification du score par rapport au seuil défini
                    if best_score < threshold:
                        best_match = "Aucune correspondance"

                detection_results.append({
                    "page": page_number + 1,
                    "image_index": img_index,
                    "best_match": best_match,
                    "score": best_score
                })

        return {"status": "Détection terminée", "results": detection_results}

    except Exception as e:
        logger.error(f"Erreur lors de la détection des éléments : {str(e)}")
        return HTTPException(status_code=500, detail=f"Erreur lors de la détection des éléments : {str(e)}")
