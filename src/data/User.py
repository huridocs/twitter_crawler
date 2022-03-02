from pydantic import BaseModel


class User(BaseModel):
    author_id: int
    user_name: str
    user_alias: str

    @staticmethod
    def from_response(response, author_id: int):
        users = {u["id"]: u for u in response.includes["users"]}
        return User(author_id=author_id, user_name=users[author_id].name, user_alias=users[author_id].username)
