import asyncio
import logging
import os

from core import builds_crud
from models.database import database

logger = logging.getLogger('beholder')
logger.setLevel(logging.INFO)


def fallen(pid):
    if pid is None:
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return True
    return False


async def check(task):
    fallen_app = fallen(task['app_pid'])
    if fallen_app:
        await builds_crud.update(task['id'], dict(status='stopped'))


async def watch_they_live():
    while True:
        await database.connect()
        tasks = await builds_crud.get_alive()
        for task in tasks:
            await check(task)
        await asyncio.sleep(0.5)
        await database.disconnect()

if __name__ == '__main__':
    asyncio.run(watch_they_live())
