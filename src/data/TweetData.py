from typing import List

from pydantic import BaseModel
from tweepy import Response

from data.Attachment import Attachment
from data.User import User
from datetime import datetime


class TweetData(BaseModel):
    created_at: int
    user: User
    text: str
    attachments: List[Attachment]
    url: str

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
                    created_at=datetime.timestamp(tweet.created_at),
                    attachments=attachments,
                )
            )

        return tweets_data
