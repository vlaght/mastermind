import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class BuildCreate(BaseModel):
    reverse_proxy_from: str = Field(
        None,
        description='Outer hostname to access application',
    )
    repository: str = Field(None, description='Project git repository')
    up_command: str = Field(
        None,
        description='Command to launch application with %PORT% placeholder',
    )
    build_command: Optional[str] = Field(
        None,
        description='Command to build application if needed',
    )


class Build(BaseModel):
    id: int
    name: str
    reverse_proxy_to: str = Field(None, description='Application url')
    reverse_proxy_from: str
    repository: str
    up_command: str
    build_command: Optional[str] = None
    port: Optional[int] = None
    path: str
    app_pid: Optional[int] = None
    reverse_proxy_pid: Optional[int] = None
    log: Optional[str] = None
    status: str
    created_dt: datetime.datetime
    updated_dt: datetime.datetime
    build_time: Optional[float] = None


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
