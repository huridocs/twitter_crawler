from pydantic import BaseModel


class Params(BaseModel):
    search: str
    fromUTCTimestamp: int
