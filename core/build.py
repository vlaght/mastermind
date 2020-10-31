import asyncio
import datetime
import hashlib
import logging

# from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy import or_

from core.base import Crud as BaseCrud
from core.utils import clone_repo
from core.utils import silent_kill
from models.database import database

logger = logging.getLogger('builds_core')
logger.setLevel(logging.INFO)


class BuildsCrud(BaseCrud):

    async def stop_existent(self, values):
        logger.info('Looking for existent build')
        statement = self.table.select().where(
            and_(
                self.table.c.repository == values['repository'],
                or_(
                    self.table.c.status == 'pending',
                    self.table.c.status == 'working',
                )
            )
        )
        async with database.transaction():
            all_previous_builds = await database.fetch_all(query=statement)
            logger.info(
                'Found existent builds to stop: %d',
                len(all_previous_builds)
            )
            for build in all_previous_builds:
                silent_kill(build['app_pid'])

    async def create(self, values):
        await asyncio.wait_for(self.stop_existent(values), None)
        hasher = hashlib.sha256()
        hasher.update(str(values).encode())
        hasher.update(str(datetime.datetime.now()).encode())
        path = 'builds/{}'.format(hasher.hexdigest())
        values['path'] = path
        if not values.get('name'):
            name = values['repository'].split('/')[-1]
            name = name.replace('.git', '')
            values['name'] = name
        clone_repo(values)
        values['status'] = 'pending'
        return await super().create(values)

    async def find_one(self):
        statement = self.table.select().where(
            and_(
                self.table.c.status == 'pending',
                ~self.table.c.deleted,
            )
        )
        async with database.transaction():
            selected = await database.fetch_one(query=statement)
            if selected:
                selected = await self.update(
                    selected['id'],
                    dict(status='running')
                )
        return selected

    async def get_alive(self):
        statement = self.table.select().where(
            or_(
                and_(
                    self.table.c.app_pid.isnot(None),
                ),
                self.table.c.status == 'running',
            )
        )
        return await database.fetch_all(query=statement)

    async def get_working(self):
        statement = self.table.select().where(
            and_(
                self.table.c.app_pid.isnot(None),
                self.table.c.status == 'working',
            )
        )
        return await database.fetch_all(query=statement)
