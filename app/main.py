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

app = FastAPI()

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
app.include_router(session.router)
app.include_router(student.router)
app.include_router(teacher.router)
app.include_router(user_session.router)
app.include_router(user.router)


@app.get("/")
def index():
    return "Welcome to Portal!"


handler = Mangum(app)
