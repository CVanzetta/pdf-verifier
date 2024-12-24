from flask import Flask, request, jsonify
from pdf2image import convert_from_path
import cv2
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
    image_path = "page1.jpg"
    images[0].save(image_path)  # Sauvegarde la première page comme image

    # Vérification du logo avec OpenCV
    logo_path = "logo_reference.png"  # Image de référence du logo
    logo_found = check_logo(image_path, logo_path)

    return jsonify({"logo_found": logo_found})

def check_logo(image_path, logo_path, threshold=0.8):
    # Charger l'image et le logo
    image = cv2.imread(image_path, 0)
    logo = cv2.imread(logo_path, 0)

    # Correspondance avec le modèle
    result = cv2.matchTemplate(image, logo, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)

    return max_val >= threshold

if __name__ == '__main__':
    app.run(debug=True)
