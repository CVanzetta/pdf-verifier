from flask import Flask, request, jsonify
from pdf2image import convert_from_path  # type: ignore
import cv2  # type: ignore
import os

app = Flask(__name__)

# Route pour vérifier le logo
@app.route('/verify-logo', methods=['POST'])
def verify_logo():
    # Charger le fichier PDF
    pdf_file = request.files['file']
    pdf_path = "uploaded.pdf"
    pdf_file.save(pdf_path)

    # Convertir le PDF en images
    images = convert_from_path(pdf_path, dpi=300)
    logo_path = "logo_reference.png"  # Image de référence du logo

    # Vérification du logo sur toutes les pages
    all_pages_verified = True
    for i, image in enumerate(images):
        image_path = f"page_{i + 1}.jpg"
        image.save(image_path)  # Sauvegarde chaque page comme image

        # Vérification du logo avec OpenCV
        logo_found = check_logo(image_path, logo_path)
        if not logo_found:
            all_pages_verified = False
            break

    return jsonify({"all_pages_verified": all_pages_verified})

def check_logo(image_path, logo_path, threshold=0.8):
    # Charger l'image et le logo
    image = cv2.imread(image_path, 0)
    logo = cv2.imread(logo_path, 0)

    # Appliquer la méthode de correspondance de modèle
    result = cv2.matchTemplate(image, logo, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Vérifier si le logo est trouvé avec un seuil
    if max_val >= threshold:
        return True
    else:
        return False

if __name__ == '__main__':
    app.run(debug=True)