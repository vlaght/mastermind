from typing import List

from pydantic import BaseModel


def get_page_schema(type_):

    class Page(BaseModel):
        limit: int
        total: int
        page: int
        last_page: int
        items: List[type_]

    return Page
