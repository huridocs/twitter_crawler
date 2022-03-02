from typing import List
from tweepy import Response

from Attachment import Attachment
from User import User


class TweetData:
    def __init__(self, text: str, user: User, url: str, created_at, attachments: List[Attachment]):
        self.attachments = attachments
        self.created_at = created_at
        self.text = text
        self.user = user
        self.url = url

    @staticmethod
    def from_tweets_list(response: Response) -> List["TweetData"]:
        tweets_data = list()
        for tweet in response.data:
            user = User.from_response(response, tweet.author_id)
            attachments = Attachment.from_response(response, tweet.data)
            tweets_data.append(
                TweetData(
                    text=tweet.text,
                    user=user,
                    url=f"https://twitter.com/{user.user_alias}/statuses/{tweet.id}",
                    created_at=tweet.created_at,
                    attachments=attachments,
                )
            )

        return tweets_data
