# server/app/routes/pdf_extract.py

import os
import fitz  # PyMuPDF
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

EXTRACTED_IMAGES_DIR = "extracted_images"
os.makedirs(EXTRACTED_IMAGES_DIR, exist_ok=True)

@router.post("/extract-images")
async def extract_images_from_pdf(file: UploadFile = File(...)):
    """Extrait les images intégrées dans le PDF."""
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
                if not base_image:
                    continue
                image_bytes = base_image["image"]
                image_filename = os.path.join(EXTRACTED_IMAGES_DIR, f"page_{page_number+1}_img_{img_index}.png")
                with open(image_filename, "wb") as image_file:
                    image_file.write(image_bytes)
                # Tentative de récupération de la bbox
                try:
                    bbox = page.get_image_bbox(xref)
                    position = {"x0": bbox.x0, "y0": bbox.y0, "x1": bbox.x1, "y1": bbox.y1}
                except Exception:
                    position = None

                image_positions.append({
                    "page": page_number + 1,
                    "image_index": img_index,
                    "image_path": image_filename,
                    "position": position
                })

        return {"status": "Extraction réussie", "images": image_positions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur extraction images : {str(e)}")
