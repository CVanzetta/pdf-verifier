import json
from pathlib import Path
import cv2
import numpy as np

SERVER_DIR = Path(__file__).resolve().parents[2]
REFERENCE_MODELS_DIR = SERVER_DIR / "reference_models"
REFERENCE_BBOXES_FILE = SERVER_DIR / "reference_bboxes.json"

def load_reference_images():
    """Charge les images de référence depuis le dossier reference_models."""
    models = {}
    if not REFERENCE_MODELS_DIR.is_dir():
        return models

    for model_path in REFERENCE_MODELS_DIR.iterdir():
        if model_path.is_file():
            image = cv2.imread(str(model_path), cv2.IMREAD_GRAYSCALE)
            if image is not None:
                models[model_path.name] = image
    return models

def load_reference_bboxes():
    """Charge les positions attendues depuis un fichier JSON local facultatif."""
    if not REFERENCE_BBOXES_FILE.is_file():
        return {}
    with REFERENCE_BBOXES_FILE.open(encoding="utf-8") as config_file:
        return json.load(config_file)

def match_images(extracted_image, reference_images, method="ORB"):
    """
    Compare l'image extraite aux modèles de référence via ORB/SIFT 
    et retourne le meilleur match + le score.
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
            # En ORB => NORM_HAMMING, en SIFT => NORM_L2
            norm = cv2.NORM_HAMMING if method == "ORB" else cv2.NORM_L2
            bf = cv2.BFMatcher(norm, crossCheck=True) if method == "ORB" else cv2.BFMatcher()
            matches = bf.match(des1, des2)
            score = len(matches)
            if score > best_score:
                best_score = score
                best_match = model_name

    return best_match, best_score

def compute_homography_bbox(extracted_image, template, method="ORB", ransac_thresh=5.0, ratio_thresh=0.75):
    """
    Calcule l'homographie entre l'image extraite et le template pour obtenir la bounding box.
    """
    detector = cv2.ORB_create() if method == "ORB" else cv2.SIFT_create()
    kp1, des1 = detector.detectAndCompute(extracted_image, None)
    kp2, des2 = detector.detectAndCompute(template, None)

    if des1 is None or des2 is None:
        return None

    norm = cv2.NORM_HAMMING if method == "ORB" else cv2.NORM_L2
    bf = cv2.BFMatcher(norm)
    matches = bf.knnMatch(des1, des2, k=2)

    good = []
    for m, n in matches:
        if m.distance < ratio_thresh * n.distance:
            good.append(m)

    if len(good) >= 4:
        pts_src = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        pts_dst = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        H, _ = cv2.findHomography(pts_dst, pts_src, cv2.RANSAC, ransac_thresh)
        if H is not None:
            h, w = template.shape[:2]
            pts = np.float32([[0,0], [0,h-1], [w-1,h-1], [w-1,0]]).reshape(-1,1,2)
            dst = cv2.perspectiveTransform(pts, H)
            min_x = float(dst[:,0,0].min())
            min_y = float(dst[:,0,1].min())
            max_x = float(dst[:,0,0].max())
            max_y = float(dst[:,0,1].max())
            return {
                "left": min_x,
                "top": min_y,
                "width": max_x - min_x,
                "height": max_y - min_y
            }
    return None

def is_within_margin(ref_bbox, comp_bbox, margin):
    """Vérifie si la bbox détectée est dans une marge d'erreur par rapport à la bbox de référence."""
    diff_left = abs(ref_bbox["left"] - comp_bbox["left"])
    diff_top = abs(ref_bbox["top"] - comp_bbox["top"])
    diff_width = abs(ref_bbox["width"] - comp_bbox["width"])
    diff_height = abs(ref_bbox["height"] - comp_bbox["height"])
    within = (diff_left <= margin and diff_top <= margin 
              and diff_width <= margin and diff_height <= margin)
    return within, {
        "left": diff_left,
        "top": diff_top,
        "width": diff_width,
        "height": diff_height
    }
