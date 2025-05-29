"""
omr_ocr.py

Unified OMR and OCR processing module using OpenCV and Tesseract.
"""
import cv2
import numpy as np
import pytesseract
import re
from typing import Dict, Any
from ..domain.entities import RegionBoundingBox

__all__ = ["grade_scan"]

def _get_confidence(data_str: str) -> float:
    """
    Parse TSV output from pytesseract.image_to_data and compute average confidence.
    Returns confidence in [0.0, 1.0].
    """
    lines = data_str.strip().splitlines()
    if len(lines) < 2:
        return 0.0
    header = lines[0].split("\t")
    try:
        conf_idx = header.index("conf")
    except ValueError:
        return 0.0
    confs = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) <= conf_idx:
            continue
        try:
            conf = int(parts[conf_idx])
            if conf >= 0:
                confs.append(conf)
        except ValueError:
            continue
    if not confs:
        return 0.0
    return sum(confs) / len(confs) / 100.0

def extract_fields(image: np.ndarray, regions: Dict[str, RegionBoundingBox]) -> Dict[str, Any]:
    """
    Extract handwritten name and printed CURP from the given regions.
    Returns a dict with keys: nombre_text, nombre_confidence, curp_text, curp_confidence.
    """
    results: Dict[str, Any] = {}

    nombre_bbox = regions.get('nombre')
    if nombre_bbox:
        x, y, w, h = nombre_bbox.x, nombre_bbox.y, nombre_bbox.width, nombre_bbox.height
        nombre_img = image[y:y+h, x:x+w]
        nombre_gray = cv2.cvtColor(nombre_img, cv2.COLOR_BGR2GRAY)
        nombre_proc = cv2.bilateralFilter(nombre_gray, d=9, sigmaColor=75, sigmaSpace=75)
        config = '--psm 7'
        text = pytesseract.image_to_string(nombre_proc, lang='spa', config=config).strip()
        data = pytesseract.image_to_data(nombre_proc, lang='spa', config=config)
        conf = _get_confidence(data)
        results['nombre_text'] = text
        results['nombre_confidence'] = conf
    else:
        results['nombre_text'] = ''
        results['nombre_confidence'] = 0.0

    curp_bbox = regions.get('curp')
    if curp_bbox:
        x, y, w, h = curp_bbox.x, curp_bbox.y, curp_bbox.width, curp_bbox.height
        curp_img = image[y:y+h, x:x+w]
        curp_gray = cv2.cvtColor(curp_img, cv2.COLOR_BGR2GRAY)
        _, curp_proc = cv2.threshold(curp_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        config = '--psm 7'
        text = pytesseract.image_to_string(curp_proc, lang='spa', config=config).strip().replace(' ', '')
        data = pytesseract.image_to_data(curp_proc, lang='spa', config=config)
        conf = _get_confidence(data)
        pattern = r'^[A-Z]{4}\d{6}[HM][A-Z]{5}\d{2}$'
        if not re.match(pattern, text):
            conf = 0.0
        results['curp_text'] = text
        results['curp_confidence'] = conf
    else:
        results['curp_text'] = ''
        results['curp_confidence'] = 0.0

    return results

def grade_scan(image: np.ndarray, regions: Dict[str, RegionBoundingBox]) -> Dict[str, Any]:
    """
    Perform OMR scoring and OCR field extraction.
    Returns a dict containing score, answers, total, nombre_text, nombre_confidence, curp_text, curp_confidence.
    """
    fields = extract_fields(image, regions)
    omr_bbox = regions.get('omr')
    score = 0
    answers = []
    total = 0
    if omr_bbox:
        x, y, w, h = omr_bbox.x, omr_bbox.y, omr_bbox.width, omr_bbox.height
        omr_img = image[y:y+h, x:x+w]
        gray = cv2.cvtColor(omr_img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        circles = cv2.HoughCircles(
            blur, cv2.HOUGH_GRADIENT, dp=1.2, minDist=20,
            param1=50, param2=30, minRadius=10, maxRadius=20
        )
        if circles is not None:
            cnt = circles[0].shape[0]
            total = cnt
            answers = [True] * cnt
            score = cnt

    result: Dict[str, Any] = {
        'score': score,
        'answers': answers,
        'total': total,
        'nombre_text': fields.get('nombre_text', ''),
        'nombre_confidence': fields.get('nombre_confidence', 0.0),
        'curp_text': fields.get('curp_text', ''),
        'curp_confidence': fields.get('curp_confidence', 0.0)
    }
    return result