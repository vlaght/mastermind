from core import builds_crud
from schemas.builds import Dispatcher as BuildsDispatcher

from .base import bind_crud_handlers


def bind_handlers(app):
    bind_crud_handlers(
        app,
        'builds',
        BuildsDispatcher,
        builds_crud,
        exclude=['update', 'delete'],
    )

    @app.get("/")
    async def read_root():
        return {"Hello": "World"}
