from fastapi import APIRouter, UploadFile, File, HTTPException
from pdf2image import convert_from_bytes
from ..utils.image_processing import preprocess_image, extract_text_with_positions, extract_text

router = APIRouter()

@router.post("/analyze-text")
async def analyze_pdf(file: UploadFile = File(...)):
    """Extrait le texte via OCR."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    try:
        pdf_bytes = await file.read()
        images = convert_from_bytes(pdf_bytes)
        extracted_text = []
        for i, img in enumerate(images):
            processed_img = preprocess_image(img)
            text = extract_text(processed_img)
            extracted_text.append({"page": i + 1, "text": text})
        return {"status": "Analyse réussie", "text_data": extracted_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur OCR : {str(e)}")

@router.post("/verify-positions")
async def verify_text_positions(file: UploadFile = File(...)):
    """
    Vérifie les positions de certains mots-clés (exemple : "361", "réduction multie-équipement") 
    via l'extraction de texte et leur bounding box.
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

                # Exemple de test sur "logo"
                if "logo" in text:
                    status = "Passed" if (position["left"] < 100 and position["top"] < 100) else "Failed"
                    position_results.append({
                        "page": i + 1,
                        "element": text,
                        "status": status,
                        "position": position,
                        "expected_position": "En haut à gauche (left < 100, top < 100)"
                    })

                # Exemple de test sur "signature" en page 1
                if i == 0 and "signature" in text:
                    page_height = 1000  # Valeur arbitraire à adapter
                    status = "Passed" if (position["top"] > page_height * 0.75) else "Failed"
                    position_results.append({
                        "page": i + 1,
                        "element": text,
                        "status": status,
                        "position": position,
                        "expected_position": "En bas de la première page"
                    })

        return {"status": "Vérification terminée", "results": position_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la vérification des positions : {str(e)}")
