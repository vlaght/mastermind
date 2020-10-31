import asyncio
import datetime
import hashlib
import logging
import os
import subprocess

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy import or_

from core.base import Crud as BaseCrud
from models.database import database

logger = logging.getLogger('builds_core')
logger.setLevel(logging.INFO)


def clone_repo(values):

    git_clone_args = [
        'git',
        'clone',
        values['repository'],
        values['path'],
    ]
    res = subprocess.run(git_clone_args)
    if res.returncode != 0:
        msg = 'Failed to clone repository, check server logs.'
        raise HTTPException(500, detail=msg)


class BuildsCrud(BaseCrud):

    def silent_kill(self, pid):
        logger.info('Trying to kill process by pid: %d', pid)
        if pid is None:
            return
        try:
            os.kill(pid, 9)
        except OSError:
            logger.info('Process %d not found', pid)

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
                self.silent_kill(build['app_pid'])
                self.silent_kill(build['reverse_proxy_pid'])

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
                    self.table.c.reverse_proxy_pid.isnot(None),
                ),
                self.table.c.status == 'running',
            )
        )
        return await database.fetch_all(query=statement)
