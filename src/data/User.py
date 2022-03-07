from pydantic import BaseModel


class User(BaseModel):
    author_id: int
    name: str
    alias: str
    display_name: str
    url: str

    @staticmethod
    def from_response(response, author_id: int):
        users = {u["id"]: u for u in response.includes["users"]}
        return User(
            author_id=author_id,
            name=users[author_id].name,
            alias=users[author_id].username,
            display_name=" ".join([users[author_id].name, f"@{users[author_id].username}"]),
            url=f"https://twitter.com/{users[author_id].username}",
        )
