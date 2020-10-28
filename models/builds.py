from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Enum
from sqlalchemy import Table
from sqlalchemy import false
from sqlalchemy import func

from .database import metadata

statuses = (
    'pending',
    'failing',
    'stopped',
    'running',
    'retired'
)

Build = Table(
    'Build',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('reverse_proxy_to', String, nullable=True),
    Column('reverse_proxy_from', String, nullable=True),
    Column('repository', String, nullable=True),
    Column('up_command', String, nullable=True),
    Column('port', Integer, nullable=True),
    Column('path', String, nullable=True),
    Column('log', Text, nullable=True),
    Column('status', Enum(statuses, name='build_status'), nullable=False),
    Column(
        'created_dt',
        DateTime,
        nullable=False,
        default=func.now(),
    ),
    Column(
        'updated_dt',
        DateTime,
        nullable=False,
        default=func.now(),
    ),
)
