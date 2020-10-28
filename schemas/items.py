import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class BuildCreate(BaseModel):
    name: str = Field(None, description='Name of project')
    reverse_proxy_to: str = Field(None, description='Application url')
    reverse_proxy_from: str = Field(
        None,
        description='Outer hostname to access application',
    )
    repository: str = Field(None, description='Project git repository')
    up_command: str = Field(
        None,
        description='Command to launch application with %PORT% placeholder',
    )


class Build(BaseModel):
    id: int
    name: str
    reverse_proxy_to: str
    reverse_proxy_from: str
    repository: str
    up_command: str
    port: int
    path: str
    log: str
    status: str
    created_dt: datetime.datetime
    updated_dt: datetime.datetime


class BuildReadPage(BaseModel):
    id: int
    name: str
    reverse_proxy_from: str
    status: str
    created_dt: datetime.datetime


class Dispatcher:
    create = BuildCreate
    update = None
    read = Build
    read_page = BuildReadPage
