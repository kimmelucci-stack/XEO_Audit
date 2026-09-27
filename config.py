from pathlib import Path
import os


# Project
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_ROOT = PROJECT_ROOT / "data"


# Crawl scope
CRAWL_TARGET = 50
CRAWL_HARD_CAP = 50
CRAWL_MIN_DESIRED = 25


# HTTP
HTTP_TIMEOUT_SECONDS = 15
HTTP_MAX_RETRIES = 2
CRAWL_DELAY_SECONDS = 1.0
USER_AGENT = "XEOAudit/1.0"


# Device
DEFAULT_DEVICE = "mobile"
ALLOWED_DEVICES = (
    "mobile",
    "desktop",
)


# Performance
PERFORMANCE_SAMPLE_SIZE = 4
GOOGLE_API_KEY = (
    os.getenv("GOOGLE_API_KEY")
    or os.getenv("PAGESPEED_API_KEY")
)


# External intelligence providers
DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
