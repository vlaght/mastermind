import datetime
import hashlib
import subprocess

from fastapi import HTTPException
from sqlalchemy import and_

from core.base import Crud as BaseCrud
from models.database import database


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

    async def create(self, values):
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
