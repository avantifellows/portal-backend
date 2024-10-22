from router import (
    auth_group,
    auth,
    batch,
    enrollment_record,
    form,
    group_session,
    group_user,
    group,
    school,
    session_occurrence,
    session,
    student,
    teacher,
    user_session,
    user,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_jwt_auth.exceptions import AuthJWTException
from mangum import Mangum
import settings
import random
import string
import time
from logger_config import setup_logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Depends

logger = setup_logger()

RATE_LIMITING_ENABLED = True

app = FastAPI()

limiter = Limiter(
    key_func=get_remote_address,
    strategy="fixed-window",
    storage_uri="memory://",
    enabled=RATE_LIMITING_ENABLED,
)

app.state.limiter = limiter

# Add rate limiting middleware
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(
        f"Rate limit exceeded - IP: {get_remote_address(request)}, "
        f"Path: {request.url.path}, "
        f"Method: {request.method}"
    )
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded", "retry_after": str(exc.retry_after)},
    )


# Define rate limit decorators for different endpoints
def auth_rate_limit():
    return limiter.limit(
        "100 per minute", error_message="Authentication rate limit exceeded"
    )


def user_rate_limit():
    return limiter.limit(
        "100 per minute", error_message="User endpoint rate limit exceeded"
    )


auth.router.dependencies.append(Depends(auth_rate_limit()))
user.router.dependencies.append(Depends(user_rate_limit()))


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Intercepts all http requests and logs their details like
    path, method, headers, time taken by request etc.
    Each request is assigned a random id (rid) which is used
    to track the request in logs.
    """
    # random id for request so that we can track it in logs
    idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(
        f"rid={idem} start request path={request.url.path} method={request.method} headers={request.headers}"
    )
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)
    logger.info(
        f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}"
    )

    return response


origins = [
    "http://localhost:8080",
    "http://localhost:3000",
    "https://staging-auth.avantifellows.org",
    "https://auth.avantifellows.org",
    "https://staging-gurukul.avantifellows.org",
    "https://gurukul.avantifellows.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(user.router, prefix="/users", tags=["users"])


app.include_router(auth_group.router)
app.include_router(batch.router)
app.include_router(enrollment_record.router)
app.include_router(form.router)
app.include_router(group_session.router)
app.include_router(group_user.router)
app.include_router(group.router)
app.include_router(school.router)
app.include_router(session_occurrence.router)
app.include_router(session.router)
app.include_router(student.router)
app.include_router(teacher.router)
app.include_router(user_session.router)


@app.get("/")
@limiter.limit("100 per minute")
async def index(request: Request):  # Added request parameter and made it async
    return "Welcome to Portal!"


handler = Mangum(app)
