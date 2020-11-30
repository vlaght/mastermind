import os

import databases
import sqlalchemy

from cfg import DATABASE_URLS

metadata = sqlalchemy.MetaData()


def get_db(target: str = 'main'):
    return databases.Database(DATABASE_URLS[target])


def get_engine(target: str = 'main'):
    return sqlalchemy.create_engine(DATABASE_URLS[target])


database = get_db('test') if os.getenv('TESTING') else get_db()
