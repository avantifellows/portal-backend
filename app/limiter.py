from slowapi import Limiter
from slowapi.util import get_remote_address

# Global SlowAPI limiter instance. Shared across routers via ``from limiter import limiter``.
# Uses the client's remote address as the rate-limit key.
limiter = Limiter(key_func=get_remote_address)
