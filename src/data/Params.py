from pydantic import BaseModel


class Params(BaseModel):
    query: str
    from_UTC_timestamp: int
