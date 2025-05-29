"""
Image processing utilities for document enhancement and region detection.
"""
import cv2
import numpy as np

from typing import Dict
from ..domain.entities import RegionBoundingBox


class ImageProcessor:
    """
    Handles document image enhancement and simple region detection.
    Stub implementations provided; replace with real OpenCV logic.
    """
    async def enhance_document_image(self, image: np.ndarray) -> np.ndarray:
        """
        Apply image enhancement: denoise with bilateral filter and apply CLAHE.
        Returns a color image ready for region detection.
        """
        # Denoise with bilateral filter
        denoised = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)
        # Convert to LAB color space for CLAHE on the L channel
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        merged = cv2.merge((cl, a, b))
        # Convert back to BGR
        enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        return enhanced

    async def detect_document_regions(
        self, processed: np.ndarray
    ) -> Dict[str, RegionBoundingBox]:
        """
        Detect document boundary via contour approximation, then compute
        relative regions for bubbles (OMR), name, and CURP.
        """
        h, w = processed.shape[:2]
        # Edge detection to find document outline
        gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        doc_cnt = None
        for c in sorted(contours, key=cv2.contourArea, reverse=True):
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                doc_cnt = approx
                break
        if doc_cnt is not None:
            x, y, w_box, h_box = cv2.boundingRect(doc_cnt)
        else:
            x, y, w_box, h_box = 0, 0, w, h
        # Compute relative ROIs
        roi_x = x + int(0.05 * w_box)
        roi_w = int(0.90 * w_box)
        name_y = y + int(0.05 * h_box)
        name_h = int(0.10 * h_box)
        curp_y = y + int(0.17 * h_box)
        curp_h = int(0.10 * h_box)
        omr_y = y + int(0.30 * h_box)
        omr_h = h_box - (omr_y - y)
        return {
            'omr': RegionBoundingBox(x=roi_x, y=omr_y, width=roi_w, height=omr_h),
            'nombre': RegionBoundingBox(x=roi_x, y=name_y, width=roi_w, height=name_h),
            'curp': RegionBoundingBox(x=roi_x, y=curp_y, width=roi_w, height=curp_h),
        }

    async def optimize_for_handwriting(self, region_img: np.ndarray) -> np.ndarray:
        """
        Preprocess region image for handwritten name OCR.
        """
        # TODO: apply binarization, denoising
        return region_img

    async def optimize_for_print_text(self, region_img: np.ndarray) -> np.ndarray:
        """
        Preprocess region image for printed CURP OCR.
        """
        # TODO: apply thresholding, sharpening
        return region_img