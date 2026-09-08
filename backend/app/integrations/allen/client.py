import logging
import re
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel
from app.config import get_settings
from app.processing.extractor import PDFTextExtractor
from app.integrations.allen.mock_data import (
    MOCK_ALLEN_TEST_CARDS,
    get_mock_question_paper_pdf_bytes,
    get_mock_syllabus_pdf_bytes,
)

logger = logging.getLogger(__name__)


class RawAllenTestCard(BaseModel):
    test_id: str
    title: str
    status: Optional[str] = None
    date_str: Optional[str] = None
    duration_minutes: Optional[int] = None
    mode: Optional[str] = None
    category: Optional[str] = None
    syllabus_uri: Optional[str] = None
    raw_card: Dict[str, Any] = {}


class AllenClient:
    """External source adapter for the ALLEN Live student portal.
    
    Supports both offline mock execution (for testing and local dev) and live
    authenticated API calls against api.allen-live.in.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        mock_mode: Optional[bool] = None,
        timeout: Optional[float] = None,
        course_id: Optional[str] = None,
        batch_list: Optional[str] = None,
        client_type: Optional[str] = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.ALLEN_BASE_URL).rstrip("/")
        self.auth_token = auth_token if auth_token is not None else settings.ALLEN_AUTH_TOKEN
        self.mock_mode = mock_mode if mock_mode is not None else (settings.ALLEN_MOCK_MODE or not bool(self.auth_token))
        self.timeout = timeout or settings.REQUEST_TIMEOUT_SECONDS
        self.course_id = course_id or settings.ALLEN_COURSE_ID
        self.batch_list = batch_list or settings.ALLEN_BATCH_LIST
        self.client_type = client_type or settings.ALLEN_CLIENT_TYPE

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36",
            "Referer": "https://allen.in/",
            "Origin": "https://allen.in",
        }
        settings = get_settings()
        client_type = self.client_type or settings.ALLEN_CLIENT_TYPE
        if client_type:
            headers["x-client-type"] = client_type
        if settings.ALLEN_DEVICE_ID:
            headers["x-device-id"] = settings.ALLEN_DEVICE_ID
        
        batch_list = self.batch_list or settings.ALLEN_BATCH_LIST
        if batch_list:
            headers["x-selected-batch-list"] = batch_list

        course_id = self.course_id or settings.ALLEN_COURSE_ID
        if course_id:
            headers["x-selected-course-id"] = course_id

        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    @classmethod
    def parse_test_card(cls, card: Dict[str, Any]) -> RawAllenTestCard:
        """Extracts normalized metadata from an observed ALLEN test card dictionary."""
        test_id = str(card.get("test_id", ""))
        title = str(card.get("title", f"Test {test_id}"))
        status = card.get("status")
        category = card.get("category")

        date_str = None
        duration_minutes = None
        mode = None

        labels = card.get("labels", [])
        for label_obj in labels:
            text = label_obj.get("text", "").strip()
            # Duration check (e.g., "180 Min", "200 Mins")
            dur_match = re.search(r"(\d+)\s*Min", text, re.IGNORECASE)
            if dur_match:
                duration_minutes = int(dur_match.group(1))
                continue

            # Mode check (e.g. "Offline", "Online", "CBT")
            if text.lower() in ["offline", "online", "cbt"]:
                mode = text
                continue

            # Otherwise date label (e.g. "13 Sep")
            if not date_str and any(m in text.lower() for m in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                date_str = text

        # Syllabus action URI
        syllabus_uri = None
        link_cta = card.get("link_cta", {})
        action_data = link_cta.get("action", {}).get("data", {})
        if "uri" in action_data:
            syllabus_uri = action_data["uri"]

        return RawAllenTestCard(
            test_id=test_id,
            title=title,
            status=status,
            date_str=date_str,
            duration_minutes=duration_minutes,
            mode=mode,
            category=category,
            syllabus_uri=syllabus_uri,
            raw_card=card
        )

    async def list_tests(
        self,
        status: str = "all",
        mode: str = "all",
        page_number: int = 1,
        page_size: int = 25
    ) -> List[RawAllenTestCard]:
        """Fetches a single page of the student test catalog."""
        if self.mock_mode:
            logger.info("AllenClient: operating in MOCK mode (returning fixture tests).")
            return [self.parse_test_card(c) for c in MOCK_ALLEN_TEST_CARDS]

        url = f"{self.base_url}/api/v1/tests/student-tests:byCompletionStatus"
        params = {
            "status": status,
            "mode": mode,
            "page_number": page_number,
            "page_size": page_size
        }

        logger.info(f"Fetching ALLEN tests from {url} (page {page_number})...")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params, headers=self._get_headers())
            resp.raise_for_status()
            data = resp.json()

        payload = data.get("data") or {}
        cards = payload.get("cards") or []
        return [self.parse_test_card(c) for c in cards]

    async def list_all_tests(
        self,
        status: str = "all",
        mode: str = "all",
        page_size: Optional[int] = None,
        max_pages: Optional[int] = None
    ) -> List[RawAllenTestCard]:
        """Fetches all tests across pages until no further cards are returned."""
        if self.mock_mode:
            return await self.list_tests(status=status, mode=mode)

        settings = get_settings()
        effective_page_size = page_size or settings.DEFAULT_PAGE_SIZE
        effective_max_pages = max_pages or settings.MAX_PAGES

        all_cards: List[RawAllenTestCard] = []
        seen_test_ids = set()

        for page in range(1, effective_max_pages + 1):
            page_cards = await self.list_tests(
                status=status,
                mode=mode,
                page_number=page,
                page_size=effective_page_size
            )
            if not page_cards:
                logger.info(f"No cards returned on page {page}. Concluding pagination.")
                break

            new_in_page = 0
            for card in page_cards:
                if card.test_id not in seen_test_ids:
                    seen_test_ids.add(card.test_id)
                    all_cards.append(card)
                    new_in_page += 1

            logger.info(f"Page {page}: retrieved {len(page_cards)} tests ({new_in_page} new, {len(all_cards)} total).")

            if len(page_cards) < effective_page_size:
                break

        return all_cards

    async def get_syllabus_pdf(self, test_id: str) -> Optional[bytes]:
        """Fetches the binary syllabus PDF bytes for a given test_id."""
        if self.mock_mode:
            logger.info(f"AllenClient: returning mock syllabus PDF for test {test_id}.")
            return get_mock_syllabus_pdf_bytes(test_id)

        url = f"{self.base_url}/api/v1/tests/{test_id}/syllabus?test_id={test_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=self._get_headers())
            resp.raise_for_status()
            res_data = resp.json()

            # Follow signed S3 link if provided in action data
            action_data = res_data.get("data", {}).get("action", {}).get("data", {})
            s3_url = action_data.get("uri") or res_data.get("data", {}).get("pdf_url")
            if not s3_url:
                logger.warning(f"No syllabus PDF URL returned for test {test_id}.")
                return None

            # Download the binary PDF
            try:
                pdf_resp = await client.get(s3_url)
                pdf_resp.raise_for_status()
                return PDFTextExtractor.sanitize_pdf_bytes(pdf_resp.content)
            except Exception as pdf_err:
                logger.warning(f"Failed to download syllabus PDF for test {test_id} from {s3_url}: {pdf_err}")
                return None

    async def get_question_paper_pdf(self, test_id: str) -> Optional[bytes]:
        """Fetches the question paper / solution PDF from result-insights endpoint."""
        if self.mock_mode:
            logger.info(f"AllenClient: returning mock question paper PDF for test {test_id}.")
            return get_mock_question_paper_pdf_bytes(test_id)

        url = f"{self.base_url}/api/v1/tests/{test_id}/result-insights?attempt=0"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code in [400, 403, 404, 500]:
                    logger.info(f"Question paper/result-insights not available yet for test {test_id} (status: {resp.status_code}).")
                    return None
                resp.raise_for_status()
                res_data = resp.json()
            except Exception as e:
                logger.info(f"Could not retrieve question paper for test {test_id}: {e}")
                return None

            # Locate English solution PDF in missed_test_info ctas
            missed_info = res_data.get("data", {}).get("missed_test_info", {})
            secondary_cta = missed_info.get("secondary_cta", {})
            ctas = secondary_cta.get("action", {}).get("data", {}).get("ctas", [])

            s3_url = None
            for cta in ctas:
                if cta.get("label", "").lower() == "english":
                    s3_url = cta.get("action", {}).get("data", {}).get("uri")
                    break

            # Fallback to first available CTA if English not specifically labeled
            if not s3_url and ctas:
                s3_url = ctas[0].get("action", {}).get("data", {}).get("uri")

            if not s3_url:
                return None

            try:
                pdf_resp = await client.get(s3_url)
                pdf_resp.raise_for_status()
                return PDFTextExtractor.sanitize_pdf_bytes(pdf_resp.content)
            except Exception as e:
                logger.warning(f"Could not download question paper PDF for test {test_id} from {s3_url}: {e}")
                return None
