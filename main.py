from router import session
from fastapi import FastAPI

app = FastAPI()

app.include_router(session.router)
