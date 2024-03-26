from starlette.requests import Request
from starlette.datastructures import Headers

def build_request(
    method: str = "GET",
    server: str = "http://127.0.0.1:8000/",
    path: str = "/",
    headers: dict = None,
    body: dict = None,
    query_params: dict = None,
) -> Request:
    if headers is None:
        headers = {}
    request = Request(
        {
            "type": "http",
            "path": path,
            "headers": Headers(headers).raw,
            "http_version": "1.1",
            "method": method,
            "scheme": "https",
            "client": ("127.0.0.1", 8080),
            "server": (server, 443),
            "query_string": query_params,
        }
    )
    if body:

        async def request_body():
            return body

        request.body = request_body
    return request
