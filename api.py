from fastapi import FastAPI

from core.utils import check_requirements
from handlers import bind_handlers
from models.database import database
from models.database import get_engine
from models.database import metadata

engine = get_engine()
metadata.create_all(bind=engine)

app = FastAPI()
bind_handlers(app)


@app.on_event("startup")
async def startup():
    check_requirements()
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
