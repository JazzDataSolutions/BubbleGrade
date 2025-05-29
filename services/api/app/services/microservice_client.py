import json
import logging
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


class MicroserviceClient:
    """
    HTTP client for communicating with external OMR and OCR microservices.
    Provides methods to process images and perform health checks.
    """
    def __init__(
        self,
        omr_url: str,
        ocr_url: str,
        timeout: float = 60.0
    ):
        self.omr_url = omr_url.rstrip('/')
        self.ocr_url = ocr_url.rstrip('/')
        self.timeout = timeout

    async def process_omr(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Send image bytes to OMR service and return the parsed JSON result.
        """
        endpoint = f"{self.omr_url}/grade"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": (filename, image_bytes, "image/jpeg")}
                response = await client.post(endpoint, files=files)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"OMR service error at {endpoint}: {e}")
            raise

    async def process_ocr(self, image_bytes: bytes, ocr_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send region image bytes and OCR parameters to OCR service.
        """
        endpoint = f"{self.ocr_url}/ocr"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"image": (ocr_request.get('region', 'region') + ".jpg", image_bytes, "image/jpeg")}
                data = {"request": json.dumps(ocr_request)}
                response = await client.post(endpoint, data=data, files=files)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"OCR service error at {endpoint}: {e}")
            raise

    async def check_omr_health(self) -> bool:
        """
        Check health endpoint of the OMR service.
        Returns True if service reports healthy, False otherwise.
        """
        endpoint = f"{self.omr_url}/health"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint)
                if response.status_code == 200:
                    body = response.json()
                    return body.get('status') == 'healthy'
        except Exception as e:
            logger.warning(f"Failed OMR health check at {endpoint}: {e}")
        return False

    async def check_ocr_health(self) -> bool:
        """
        Check health endpoint of the OCR service.
        Returns True if service reports healthy, False otherwise.
        """
        endpoint = f"{self.ocr_url}/health"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint)
                if response.status_code == 200:
                    body = response.json()
                    return body.get('status') == 'healthy'
        except Exception as e:
            logger.warning(f"Failed OCR health check at {endpoint}: {e}")
        return False