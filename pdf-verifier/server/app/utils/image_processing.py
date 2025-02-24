import cv2
import numpy as np
import pytesseract

def preprocess_image(image):
    """Convertit l'image PIL en niveaux de gris et binarise avec OpenCV."""
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def extract_text_with_positions(image):
    """Extrait le texte et ses coordonnées via Tesseract (mode data)."""
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    elements = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        if text:
            elements.append({
                "text": text,
                "position": {
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i]
                }
            })
    return elements

def extract_text(image):
    """Extrait simplement le texte (sans positions)."""
    return pytesseract.image_to_string(image)
