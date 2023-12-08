from router import (
    auth,
    session,
    group,
    student,
    session_group,
    user_session,
    session_occurrence,
    batch,
    program,
    group_type,
    form,
    user,
    teacher,
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

logger = setup_logger()

app = FastAPI()


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
    "https://staging-auth.avantifellows.org",
    "https://auth.avantifellows.org",
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


app.include_router(auth.router)
app.include_router(session.router)
app.include_router(group.router)
app.include_router(student.router)
app.include_router(session_group.router)
app.include_router(user_session.router)
app.include_router(session_occurrence.router)
app.include_router(batch.router)
app.include_router(program.router)
app.include_router(group_type.router)
app.include_router(form.router)
app.include_router(user.router)
app.include_router(teacher.router)


@app.get("/")
def index():
    return "Welcome to Portal!"


handler = Mangum(app)
