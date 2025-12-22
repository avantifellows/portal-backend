from router import (
    auth_group,
    auth,
    batch,
    candidate,
    enrollment_record,
    form,
    group_session,
    group_user,
    group,
    school,
    session_occurrence,
    abtest,
    session,
    student,
    teacher,
    user_session,
    user,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from mangum import Mangum
import random
import string
import time
from logger_config import setup_logger
from error_middleware import error_handling_middleware

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
    idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)
    logger.info(
        f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}"
    )

    return response


@app.middleware("http")
async def error_handling(request: Request, call_next):
    """
    Global error handling middleware
    """
    return await error_handling_middleware(request, call_next)


origins = [
    "http://localhost:8080",
    "http://localhost:8081",
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


app.include_router(auth_group.router)
app.include_router(auth.router)
app.include_router(batch.router)
app.include_router(enrollment_record.router)
app.include_router(form.router)
app.include_router(group_session.router)
app.include_router(group_user.router)
app.include_router(group.router)
app.include_router(school.router)
app.include_router(session_occurrence.router)
app.include_router(abtest.router)
app.include_router(session.router)
app.include_router(student.router)
app.include_router(teacher.router)
app.include_router(candidate.router)
app.include_router(user_session.router)
app.include_router(user.router)


@app.get("/")
def index():
    return "Welcome to Portal!"


handler = Mangum(app)
