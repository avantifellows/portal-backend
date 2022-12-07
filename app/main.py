from router import auth,session
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_jwt_auth.exceptions import AuthJWTException
from mangum import Mangum
import settings

app = FastAPI()

@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

app.include_router(auth.router)
app.include_router(session.router)


@app.get("/")
def index():
    return "Welcome to Portal!"


handler = Mangum(app)
