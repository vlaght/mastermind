from core import foo_crud
from schemas.items import Dispatcher as ItemDispatcher

from .base import bind_crud_handlers


def bind_handlers(app):
    bind_crud_handlers(app, 'foo', ItemDispatcher, foo_crud)

    @app.get("/")
    async def read_root():
        return {"Hello": "World"}
