from fastapi import FastAPI
from models import Hero, Ability, AbilityType, Relationship, RelationshipType
from database import engine
from sqlalchemy import select
from schemas import HeroModel, AbilityModel, AbilityTypeModel, RelationshipModel, RelationshipTypeModel
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from routers import heroes

app = FastAPI()
app.include_router(heroes.router)

origins = [
    "http://8000-coachhallso-fastapidock-5fztzl33j5c.ws-us106.gitpod.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    print(f"{repr(exc)}")
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)