from settings import Settings

"""
Centralized HTTP request configuration.

This module exists to avoid hardcoded ports/URLs and it will provide
a single source of truth for outbound HTTP requests.
"""

def get_base_url() -> str:
    return Settings.PORTAL_BASE_URL

def get_timeout() -> int:
    return Settings.REQUEST_TIMEOUT

