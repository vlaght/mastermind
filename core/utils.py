import logging
import os
import shutil
import subprocess

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def check_requirements():
    requirements = [
        'git',
        'caddy',
    ]
    not_found = ', '.join(
        [r for r in requirements if shutil.which(r) is None]
    )
    if not_found:
        logger.error(f'Following requirements aren`t satisfied: {not_found}')


def clone_repo(values):
    git_exec = shutil.which('git')
    git_clone_args = [
        git_exec,
        'clone',
        values['repository'],
        values['path'],
    ]
    res = subprocess.run(git_clone_args)
    if res.returncode != 0:
        msg = 'Failed to clone repository, check server logs.'
        raise HTTPException(500, detail=msg)


def silent_kill(pid):
    logger.info('Trying to kill process by pid: %d', pid)
    if pid is None:
        return
    try:
        os.kill(pid, 9)
    except OSError:
        logger.info('Process %d not found', pid)
