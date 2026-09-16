import cv2
import numpy as np
import fitz
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..utils.matching import load_reference_images, match_images, compute_homography_bbox

router = APIRouter()

CONFIDENCE_THRESHOLD = 10  # Exemple, à adapter à ton usage

@router.post("/detect-elements")
async def detect_elements_in_pdf(file: UploadFile = File(...), method: str = "ORB"):
    """Compare les images extraites du PDF aux modèles de référence via ORB/SIFT."""
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
                    continue
                image_bytes = base_image["image"]
                image_array = np.frombuffer(image_bytes, dtype=np.uint8)
                extracted_image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
                if extracted_image is None:
                    continue

                best_match, best_score = match_images(extracted_image, reference_images, method)

                bbox = None
                if best_match:
                    if best_score < CONFIDENCE_THRESHOLD:
                        best_match = "Aucune correspondance"
                    else:
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
        raise HTTPException(status_code=500, detail=f"Erreur lors de la détection des éléments : {str(e)}")
