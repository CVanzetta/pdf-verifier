import fitz
import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..utils.matching import (
    compute_homography_bbox,
    is_within_margin,
    load_reference_bboxes,
    load_reference_images,
    match_images,
)

router = APIRouter()

CONFIDENCE_THRESHOLD = 10  # Par défaut

@router.post("/verify-element-reference")
async def verify_element_reference(file: UploadFile = File(...), margin: int = 50, method: str = "ORB"):
    """Vérifie que les éléments détectés se trouvent aux positions de référence."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    try:
        pdf_bytes = await file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        detection_results = []

        reference_images = load_reference_images()
        reference_bboxes = load_reference_bboxes()
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
                verification = "Not Verified"
                diff_details = {}

                if best_match:
                    if best_score >= CONFIDENCE_THRESHOLD:
                        template = reference_images[best_match]
                        bbox = compute_homography_bbox(extracted_image, template, method)
                        if bbox is not None and best_match in reference_bboxes:
                            ref_bbox = reference_bboxes[best_match]
                            within, diffs = is_within_margin(ref_bbox, bbox, margin)
                            verification = "Passed" if within else "Failed"
                            diff_details = diffs
                        elif bbox is not None:
                            verification = "Position non configurée"
                        else:
                            verification = "No BBox"
                    else:
                        best_match = "Aucune correspondance"

                detection_results.append({
                    "page": page_number + 1,
                    "image_index": img_index,
                    "element": best_match,
                    "score": best_score,
                    "position": bbox,
                    "verification": verification,
                    "differences": diff_details,
                    "reference": reference_bboxes.get(best_match)
                })

        return {"status": "Vérification des positions de référence terminée", "results": detection_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la vérification des positions de référence : {str(e)}")
