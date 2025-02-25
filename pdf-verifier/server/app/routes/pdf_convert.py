import os
import uuid
import cv2
from fastapi import APIRouter, UploadFile, File, HTTPException
from pdf2image import convert_from_bytes
from ..utils.image_processing import preprocess_image

router = APIRouter()

TEMP_IMAGE_DIR = "temp_images"
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

@router.post("/convert-images")
async def convert_pdf_to_images(file: UploadFile = File(...)):
    """Convertit le PDF en images (format PNG) pour un éventuel traitement ultérieur."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    try:
        pdf_bytes = await file.read()
        images = convert_from_bytes(pdf_bytes)
        image_paths = []
        for i, img in enumerate(images):
            processed_img = preprocess_image(img)
            image_filename = os.path.join(TEMP_IMAGE_DIR, f"page_{i+1}_{uuid.uuid4().hex}.png")
            cv2.imwrite(image_filename, processed_img)
            image_paths.append(image_filename)

        return {"status": "Conversion réussie", "images": image_paths}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la conversion : {str(e)}")
