from typing import List

from pydantic import BaseModel


class Params(BaseModel):
    query: str
    tweets_languages: List[str] = list()
