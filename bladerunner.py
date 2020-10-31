import datetime
import logging
import os
import socket
import subprocess
import time

from sqlalchemy import and_
from sqlalchemy import create_engine

from models.builds import Build
from models.database import DATABASE_URLS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def free_port():
    free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    free_socket.bind(('0.0.0.0', 0))
    free_socket.listen(5)
    port = free_socket.getsockname()[1]
    free_socket.close()
    return port


def is_alive(pid):
    assert pid is not None
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def update_task(db_engine, task, values):
    statement = Build.update(None).where(Build.c.id == task['id']).values(
        **values
    ).returning(
        Build
    )
    with db_engine.connect() as conn:
        res = conn.execute(statement)
        return res.fetchone()


def build(db_engine, task):
    os.chdir(task['path'])
    build_args = task['build_command'].split(' ')
    build_start = time.perf_counter()
    try:
        res = subprocess.check_output(build_args)
    except subprocess.CalledProcessError:
        update_task(
            db_engine,
            task,
            dict(
                status='failing',
                log='Build failed. Details: {}'.format(res),
            )
        )
    build_time = (time.perf_counter() - build_start) / 10**9
    task = update_task(db_engine, task, dict(build_time=build_time))
    os.chdir(ROOT_DIR)
    return task


def construct_caddyfile(db_engine):
    select_query = Build.select().where(
        and_(
            Build.c.app_pid.isnot(None),
            Build.c.status.in_(('working', 'running')),
        )
    )
    with db_engine.connect() as conn:
        tasks = conn.execute(select_query).fetchall()
    cfg_body = [
        '{\n',
        '\tauto_https disable_redirects\n',
        '}\n\n',
    ]
    for task in tasks:
        cfg_body.extend(
            [
                '{}:80 {}\n'.format(task['reverse_proxy_from'], '{'),
                '\treverse_proxy localhost:{}\n'.format(task['port']),
                '}\n',
                '{}:443 {}\n'.format(task['reverse_proxy_from'], '{'),
                '\tredir http://{}{}\n'.format(
                    task['reverse_proxy_from'],
                    '{uri}',
                ),
                '}\n\n',
            ]
        )
    out = 'Caddyfile'
    with open(out, 'w') as cfg:
        cfg.writelines(cfg_body)
    return os.path.abspath(out)


def launch_app(task):
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
    os.chdir(ROOT_DIR)
    return app_process.pid, port


def launch_webserver(cfg_path):
    caddy_exec = subprocess.check_output(['which', 'caddy']).decode().strip()
    reverse_proxy_args = [caddy_exec, 'reload', '--config', cfg_path]
    reverse_proxy_process = subprocess.Popen(
        reverse_proxy_args,
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        # stdin=subprocess.PIPE,
        close_fds=True,
    )
    return reverse_proxy_process.pid


def start(db_engine, task):
    app_pid, port = launch_app(task)
    task = update_task(
        db_engine,
        task,
        dict(
            app_pid=app_pid,
            status='working',
            reverse_proxy_to='localhost:{}'.format(port),
            port=port,
            updated_dt=datetime.datetime.now(),
        )
    )
    cfg_path = construct_caddyfile(db_engine)
    launch_webserver(cfg_path)
    os.chdir(ROOT_DIR)

    return task


def process_exception(db_engine, task, stage, e):
    logger.error(
        'Build<id:%d> fails to %s with: %s', task['id'], stage, e
    )
    log = '{}\n{} failed: {}'.format(task['log'] or '', stage, e)
    update_task(db_engine, task, dict(status='failing', log=log))


def deal_with_bastard(task):
    db_engine = create_engine(DATABASE_URLS['main'])
    try:
        task = build(db_engine, task)
    except Exception as e:
        process_exception(db_engine, task, 'build', e)
        return
    logger.info('Build: passed')
    try:
        task = start(db_engine, task)
    except Exception as e:
        process_exception(db_engine, task, 'start', e)
        return
    logging.info('Start: successfully')


def async_build(builder, task):
    pid = os.fork()
    if pid:
        os.waitpid(pid, 0)
    else:
        if not os.fork():
            logger.info(
                'Starting asynchronous build<id:%d> (%s)',
                task['id'],
                task['repository'],
            )
            builder(task)
            logger.info(
                'Finishing build<id:%d> (%s)',
                task['id'],
                task['repository'],
            )
        os._exit(os.EX_OK)


def main():
    statement = Build.select().where(
        Build.c.status == 'pending',
    )
    db_engine = create_engine(DATABASE_URLS['main'])
    while True:
        with db_engine.connect() as db:
            task = db.execute(statement).fetchone()
        if task:
            logger.info('Build<id:%d>: processing begins', task['id'])
            async_build(deal_with_bastard, task)
        time.sleep(0.1)


if __name__ == '__main__':
    main()
