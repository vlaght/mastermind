import logging
import os
import subprocess

from fastapi import HTTPException

logger = logging.getLogger(__name__)


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


def silent_kill(pid):
    logger.info('Trying to kill process by pid: %d', pid)
    if pid is None:
        return
    try:
        os.kill(pid, 9)
    except OSError:
        logger.info('Process %d not found', pid)
