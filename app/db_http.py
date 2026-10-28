from http.cookiejar import DefaultCookiePolicy

import requests
from requests.adapters import HTTPAdapter

DEFAULT_TIMEOUT = 10


class _Session(requests.Session):
    def __init__(self):
        super().__init__()
        # db-service sits behind an ALB that sets sticky-session cookies; keeping them
        # would pin every call from this process to one db-service task.
        self.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=50)
        self.mount("https://", adapter)
        self.mount("http://", adapter)

    def request(self, *args, **kwargs):
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        return super().request(*args, **kwargs)


_session = _Session()
get = _session.get
post = _session.post
patch = _session.patch
put = _session.put
delete = _session.delete
