from typing import List

from pydantic import BaseModel

from data.TweetData import TweetData


class TweetMessage(BaseModel):
    tenant: str
    task: str
    params: TweetData
    success: bool
    error_message: str = None
    data_url: str = None
    file_url: str = None
