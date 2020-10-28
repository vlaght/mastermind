import asyncio
import logging
import os
import socket
import subprocess
import time

from core import builds_crud
from models.database import database

logger = logging.getLogger(__name__)

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
    cmd = cmd.replace('%PORT%', port)
    run_args = task['up_command'].split(' ')
    p = subprocess.Popen(
        run_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        close_fds=True,
    )
    await builds_crud.update(
        task['id'],
        dict(
            pid=p.pid,
            status='working',
            reverse_proxy_to='localhost:{}'.format(port),
            port=port,
        )
    )
    os.chdir(ROOT_DIR)


def is_alive(task):
    assert task['pid'] is not None
    try:
        os.kill(task['pid'], 0)
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
                e.args[0],
            )
        )
    )


async def launch_webserver(task):
    cmd = 'caddy reverse-proxy --from {} --to {}'.format(
        task['reverse_proxy_from'],
        task['reverse_proxy_to'],
    )
    args = cmd.split(' ')
    p = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        close_fds=True,
    )
    await builds_crud.update(
        task['id'],
        dict(
            pid=p.pid,
            status='working',
        )
    )


async def main():
    while True:
        await database.connect()
        task = await builds_crud.find_one()
        if task:
            try:
                await build(task)
            except Exception as e:
                await process_exception(task, 'build', e)
                break
            logger.info('Build: passed')
            try:
                await start(task)
            except Exception as e:
                await process_exception(task, 'start', e)
                break
            logging.info('Start: successfully')
        time.sleep(5)
        await database.disconnect()

asyncio.run(main())
