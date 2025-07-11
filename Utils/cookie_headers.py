from typing import Optional
from Utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.6422.112 Safari/537.36"
)

def generate_nse_headers(referer_url: Optional[str] = None) -> dict:
    """Generate standard NSE headers with optional Referer."""
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    if referer_url:
        headers["Referer"] = referer_url
        logger.debug(f"Generated headers with referer: {referer_url}")
    else:
        logger.debug("Generated headers without referer")

    return headers

# Optional wrapper — could remove unless needed for naming consistency
def load_nse_headers(nse_url: Optional[str] = None) -> dict:
    return generate_nse_headers(nse_url)

