from typing import List

from pydantic import BaseModel


class Params(BaseModel):
    query: str
    from_UTC_timestamp: int
    tweets_languages: List[str]
