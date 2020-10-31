import asyncio
import logging
import os
import socket
import subprocess
import time

from core import builds_crud
from models.database import database

# from multiprocessing import Process


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


async def build(task):
    os.chdir(task['path'])
    build_args = task['build_command'].split(' ')
    build_start = time.perf_counter()
    try:
        res = subprocess.check_output(build_args)
    except subprocess.CalledProcessError:
        await builds_crud.update(
            task['id'],
            dict(
                status='failing',
                log='Build failed. Details: {}'.format(res),
            )
        )
    build_time = (time.perf_counter() - build_start) / 10**9
    await builds_crud.update(
        task['id'],
        dict(
            build_time=build_time,
        )
    )
    os.chdir(ROOT_DIR)


def free_port():
    free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    free_socket.bind(('0.0.0.0', 0))
    free_socket.listen(5)
    port = free_socket.getsockname()[1]
    free_socket.close()
    return port


async def start(task):
    os.chdir(task['path'])
    cmd = task['up_command']
    port = free_port()
    cmd = cmd.replace('%PORT%', str(port))
    logger.info('Starting with: %s', cmd)
    app_args = cmd.split(' ')
    app_process = subprocess.Popen(
        app_args,
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        # stdin=subprocess.PIPE,
        close_fds=True,
    )
    caddy_exec = subprocess.check_output(['which', 'caddy']).decode().strip()
    reverse_proxy_cmd = '{} reverse-proxy --from {} --to localhost:{}'.format(
        caddy_exec,
        task['reverse_proxy_from'],
        port
    )
    reverse_proxy_args = reverse_proxy_cmd.split(' ')
    reverse_proxy_process = subprocess.Popen(
        reverse_proxy_args,
        close_fds=True,
    )
    await builds_crud.update(
        task['id'],
        dict(
            app_pid=app_process.pid,
            reverse_proxy_pid=reverse_proxy_process.pid,
            status='working',
            reverse_proxy_to='localhost:{}'.format(port),
            port=port,
        )
    )
    os.chdir(ROOT_DIR)


def is_alive(pid):
    assert pid is not None
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


async def process_exception(task, stage, e):
    logger.error(
        'Build<id:%d> fails to %s with: %s', task['id'], stage, e.args[0]
    )
    await builds_crud.update(
        task['id'],
        dict(
            status='failing',
            log='{}\n{} failed: {}'.format(
                task['log'],
                stage,
                e,
            )
        )
    )


async def deal_with_bastard(task):
    # await database.connect()
    try:
        await build(task)
    except Exception as e:
        await process_exception(task, 'build', e)
        return
    logger.info('Build: passed')
    try:
        await start(task)
    except Exception as e:
        await process_exception(task, 'start', e)
        return
    logging.info('Start: successfully')
    # await database.disconnect()


async def main():
    await database.connect()
    while True:
        task = await builds_crud.find_one()
        if task:
            logger.info('Build<id:%d>: processing begins', task['id'])
            try:
                await deal_with_bastard(task)
            except Exception as e:
                await process_exception(task, 'processing', e)
        await asyncio.sleep(0.1)


asyncio.run(main())
