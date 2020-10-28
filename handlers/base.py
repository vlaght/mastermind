from typing import Optional

from fastapi import HTTPException
from fastapi import Path
from fastapi import Query

from core.base import Crud
from schemas.base import get_page_schema


def bind_crud_handlers(app, name, schema_dispatcher, crud: Crud, exclude=[]):
    stream_url = '/{}'.format(name)
    item_url = stream_url + '/{item_id}'
    MAX_PAGE_LIMIT = 100
    ObjId = Path(
        None,
        description='identifier of object',
        ge=1
    )

    if 'read_page' not in exclude:
        @app.get(
            stream_url,
            response_model=get_page_schema(schema_dispatcher.read_page),
            tags=[name],
            operation_id='{}_read_page'.format(name),
        )
        async def read_page(
            page: Optional[int] = Query(1, ge=1),
            limit: Optional[int] = Query(
                crud.PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT
            ),
        ):
            return await crud.read_page(page=page, limit=limit)

    if 'read' not in exclude:
        @app.get(
            item_url,
            response_model=schema_dispatcher.read,
            tags=[name],
            operation_id='{}_read'.format(name),
        )
        async def read(item_id: int = ObjId):
            return await crud.read(item_id)

    if 'create' not in exclude:
        @app.post(
            stream_url,
            response_model=schema_dispatcher.read,
            tags=[name],
            operation_id='{}_create'.format(name),
        )
        async def create(
            values: schema_dispatcher.create,
        ):
            return await crud.create(values.dict())

    if 'update' not in exclude:
        @app.put(
            item_url,
            response_model=schema_dispatcher.read,
            tags=[name],
            operation_id='{}_update'.format(name),
        )
        async def update(
            item_id: int = ObjId,
            values: schema_dispatcher.update = None,
        ):
            if values is None:
                raise HTTPException(422, detail='Provide some data')
            return await crud.update(item_id, values.dict())

    if 'delete' not in exclude:
        @app.delete(
            item_url, tags=[name], operation_id='{}_delete'.format(name)
        )
        async def delete(item_id: int = ObjId):
            await crud.delete(item_id)
            return {}
