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
    fallen_proxy = fallen(task['reverse_proxy_pid'])
    fallen_app = fallen(task['app_pid'])
    if fallen_app and not fallen_proxy:
        logger.info('Build<id:%d> app down', task['id'])
        os.kill(task['reverse_proxy_pid'], 9)
    elif fallen_proxy and not fallen_app:
        logger.info('Build<id:%d> proxy down', task['id'])
        os.kill(task['app_pid'], 9)
    if any([fallen_app, fallen_proxy]):
        await builds_crud.update(task['id'], dict(status='stopped'))


async def watch_they_live():
    while True:
        await database.connect()
        tasks = await builds_crud.get_alive()
        for task in tasks:
            await check(task)
        await asyncio.sleep(0.5)
        await database.disconnect()

asyncio.run(watch_they_live())
