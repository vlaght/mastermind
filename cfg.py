import os

DATABASE_URLS = {
    'main': "postgresql://root@localhost:5432/db",
    'test': "postgresql://root@localhost:5432/db_test",
}


BUILDS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'builds'
)
