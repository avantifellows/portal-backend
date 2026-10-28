import requests

DEFAULT_TIMEOUT = 10


class _Session(requests.Session):
    def request(self, *args, **kwargs):
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        return super().request(*args, **kwargs)


_session = _Session()
get = _session.get
post = _session.post
patch = _session.patch
put = _session.put
delete = _session.delete
