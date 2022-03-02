class User:
    def __init__(self, author_id, user_name, user_alias):
        self.author_id = author_id
        self.user_name = user_name
        self.user_alias = user_alias

    @staticmethod
    def from_response(response, author_id: int):
        users = {u["id"]: u for u in response.includes["users"]}
        return User(author_id, users[author_id].name, users[author_id].username)
