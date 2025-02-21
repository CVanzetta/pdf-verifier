import json
import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from pdf2image import convert_from_bytes
import pytesseract
import shutil
import os
import uuid
import cv2  # OpenCV pour le prétraitement, la détection et le template matching
import numpy as np
import fitz  # PyMuPDF
import logging

# Dossiers supplémentaires
TEMP_RESULTS_DIR = "temp_results"
LOG_DIR = "logs"

# Création des dossiers
os.makedirs(TEMP_RESULTS_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Configuration du logger
log_file_path = os.path.join(LOG_DIR, "analysis.log")
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter()

# Dossiers de stockage
UPLOAD_DIR = "uploads"
TEMP_IMAGE_DIR = "temp_images"
EXTRACTED_IMAGES_DIR = "extracted_images"
REFERENCE_MODELS_DIR = "reference_models"  # Contient les images modèles (logo.png, signature.png, etc.)
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE_MB = 5
CONFIDENCE_THRESHOLD = 10

# Création des dossiers de stockage
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)
os.makedirs(EXTRACTED_IMAGES_DIR, exist_ok=True)
os.makedirs(REFERENCE_MODELS_DIR, exist_ok=True)

def preprocess_image(image):
    """Conversion en niveaux de gris et binarisation pour OpenCV."""
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def extract_text_with_positions(image):
    """
    Extrait le texte et ses coordonnées via OCR.
    Destiné à la vérification des positions textuelles (non utilisé pour les images).
    """
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    elements = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        if text:
            element = {
                "text": text,
                "position": {
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i]
                }
            }
            elements.append(element)
    return elements

def load_reference_images():
    """Charge les modèles de référence depuis REFERENCE_MODELS_DIR."""
    models = {}
    for model_name in os.listdir(REFERENCE_MODELS_DIR):
        model_path = os.path.join(REFERENCE_MODELS_DIR, model_name)
        models[model_name] = cv2.imread(model_path, cv2.IMREAD_GRAYSCALE)
    return models

def match_images(extracted_image, reference_images, method="ORB"):
    """
    Compare l'image extraite aux modèles de référence en utilisant ORB ou SIFT
    et retourne le meilleur modèle ainsi que son score (nombre de correspondances).
    """
    if method not in ["ORB", "SIFT"]:
        raise ValueError("Méthode non valide. Utiliser 'ORB' ou 'SIFT'.")
    detector = cv2.ORB_create() if method == "ORB" else cv2.SIFT_create()
    kp1, des1 = detector.detectAndCompute(extracted_image, None)
    best_match = None
    best_score = 0
    for model_name, model_img in reference_images.items():
        kp2, des2 = detector.detectAndCompute(model_img, None)
        if des1 is not None and des2 is not None:
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True) if method=="ORB" else cv2.BFMatcher()
            matches = bf.match(des1, des2)
            score = len(matches)
            if score > best_score:
                best_score = score
                best_match = model_name
    return best_match, best_score

def compute_homography_bbox(extracted_image, template, method="ORB", ransac_thresh=5.0, ratio_thresh=0.75):
    """
    Calcule l'homographie entre l'image extraite et le template pour obtenir la bounding box.
    Retourne la bbox sous forme de dict si suffisante, sinon None.
    """
    # Choix du détecteur
    detector = cv2.ORB_create() if method=="ORB" else cv2.SIFT_create()
    kp1, des1 = detector.detectAndCompute(extracted_image, None)
    kp2, des2 = detector.detectAndCompute(template, None)
    if des1 is None or des2 is None:
        return None
    # Utilisation de BFMatcher avec k=2 pour appliquer le ratio test
    norm = cv2.NORM_HAMMING if method=="ORB" else cv2.NORM_L2
    bf = cv2.BFMatcher(norm)
    matches = bf.knnMatch(des1, des2, k=2)
    good = []
    for m, n in matches:
        if m.distance < ratio_thresh * n.distance:
            good.append(m)
    if len(good) >= 4:
        pts_src = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        pts_dst = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
        H, mask = cv2.findHomography(pts_dst, pts_src, cv2.RANSAC, ransac_thresh)
        if H is not None:
            h, w = template.shape[:2]
            pts = np.float32([[0,0], [0,h-1], [w-1,h-1], [w-1,0]]).reshape(-1,1,2)
            dst = cv2.perspectiveTransform(pts, H)
            min_x = np.min(dst[:,0,0])
            min_y = np.min(dst[:,0,1])
            max_x = np.max(dst[:,0,0])
            max_y = np.max(dst[:,0,1])
            bbox = {"left": float(min_x), "top": float(min_y), "width": float(max_x - min_x), "height": float(max_y - min_y)}
            return bbox
    return None

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Enregistre le PDF après vérification de l'extension et de la taille."""
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
    """Convertit le PDF en images pour traitement (OCR et détection)."""
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
    """Extrait le texte via OCR après conversion du PDF en images."""
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
        raise HTTPException(status_code=500, detail=f"Erreur OCR : {str(e)}")

@router.post("/extract-images")
async def extract_images_from_pdf(file: UploadFile = File(...)):
    """
    Extrait les images intégrées dans le PDF et, si possible, leur bounding box via les métadonnées.
    (Méthode peu fiable, non utilisée pour la vérification par template matching.)
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
    try:
        pdf_bytes = await file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        image_positions = []
        for page_number, page in enumerate(pdf_document):
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                try:
                    bbox = page.get_image_bbox(xref)
                    position = {
                        "x0": bbox.x0,
                        "y0": bbox.y0,
                        "x1": bbox.x1,
                        "y1": bbox.y1
                    }
                except Exception as e:
                    logger.error(f"Erreur get_image_bbox pour xref {xref}: {str(e)}")
                    position = None
                image_filename = f"{EXTRACTED_IMAGES_DIR}/page_{page_number+1}_img_{img_index}.png"
                with open(image_filename, "wb") as image_file:
                    image_file.write(image_bytes)
                image_positions.append({
                    "page": page_number + 1,
                    "image_index": img_index,
                    "image_path": image_filename,
                    "position": position
                })
        return {"status": "Extraction réussie", "images": image_positions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur extraction images : {str(e)}")

@router.post("/detect-elements")
async def detect_elements_in_pdf(file: UploadFile = File(...), method: str = "ORB"):
    """
    Compare les images extraites du PDF aux modèles de référence via ORB/SIFT.
    En plus du score, cette version calcule l'homographie pour déterminer la position
    (bounding box) de l'élément détecté. Si le score est insuffisant, aucun élément n'est retourné.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
    try:
        pdf_bytes = await file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        detection_results = []
        reference_images = load_reference_images()
        if not reference_images:
            raise HTTPException(status_code=500, detail="Aucun modèle d'image de référence trouvé !")
        for page_number, page in enumerate(pdf_document):
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                if not base_image:
                    logger.warning(f"Impossible d'extraire l'image {img_index} de la page {page_number+1}")
                    continue
                image_bytes = base_image["image"]
                image_array = np.frombuffer(image_bytes, dtype=np.uint8)
                extracted_image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
                if extracted_image is None:
                    logger.warning(f"L'image {img_index} de la page {page_number+1} n'a pas pu être chargée.")
                    continue
                best_match, best_score = match_images(extracted_image, reference_images, method)
                bbox = None
                # Seule la correspondance est considérée si le score dépasse un seuil défini
                if best_match:
                    if "filigrane" in best_match.lower():
                        threshold = 450
                    elif "logo" in best_match.lower():
                        threshold = 450
                    elif "signature" in best_match.lower():
                        threshold = 300
                    else:
                        threshold = CONFIDENCE_THRESHOLD
                    if best_score < threshold:
                        best_match = "Aucune correspondance"
                    else:
                        # Calcul de l'homographie pour obtenir la position
                        template = reference_images[best_match]
                        bbox = compute_homography_bbox(extracted_image, template, method)
                detection_results.append({
                    "page": page_number + 1,
                    "image_index": img_index,
                    "best_match": best_match,
                    "score": best_score,
                    "position": bbox
                })
        return {"status": "Détection terminée", "results": detection_results}
    except Exception as e:
        logger.error(f"Erreur lors de la détection des éléments : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la détection des éléments : {str(e)}")

# Endpoint pour vérifier les positions textuelles (non utilisé pour les images)
@router.post("/verify-positions")
async def verify_text_positions(file: UploadFile = File(...)):
    """
    Vérifie les positions des éléments textuels (via OCR).
    Ce endpoint est destiné à la vérification du texte et n'est pas utilisé pour les images.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
    try:
        pdf_bytes = await file.read()
        images = convert_from_bytes(pdf_bytes)
        position_results = []
        for i, img in enumerate(images):
            processed_img = preprocess_image(img)
            elements = extract_text_with_positions(processed_img)
            for element in elements:
                text = element["text"].lower()
                position = element["position"]
                if "logo" in text:
                    status = "Passed" if (position["left"] < 100 and position["top"] < 100) else "Failed"
                    position_results.append({
                        "page": i+1,
                        "element": text,
                        "status": status,
                        "position": position,
                        "expected_position": "En haut à gauche (left < 100, top < 100)"
                    })
                if i == 0 and "signature" in text:
                    page_height = 1000  
                    status = "Passed" if (position["top"] > page_height * 0.75) else "Failed"
                    position_results.append({
                        "page": i+1,
                        "element": text,
                        "status": status,
                        "position": position,
                        "expected_position": "En bas de la première page"
                    })
        return {"status": "Vérification terminée", "results": position_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la vérification des positions : {str(e)}")
