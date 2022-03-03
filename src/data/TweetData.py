from typing import List

from pydantic import BaseModel
from tweepy import Response

from data.Attachment import Attachment
from data.User import User
from datetime import datetime

import re


def get_text(text: str, attachments: List[Attachment]):
    return text + '\n\n'.join([f'![{x.text}]({x.url})' for x in attachments if x.attachment_type == 'image'])


def get_hashtags(text:str):
    return re.findall( r"(#\w+)", text)


class TweetData(BaseModel):
    created_at: int
    user: User
    text: str
    images: List[str]
    source: str
    hashtags: List[str]
    title: str

    @staticmethod
    def from_tweets_list(response: Response) -> List["TweetData"]:
        tweets_data = list()
        for tweet in response.data:
            user = User.from_response(response, tweet.author_id)
            attachments = Attachment.from_response(response, tweet.data)
            tweets_data.append(
                TweetData(
                    title=f'{user.display_name} [{tweet.created_at:%Y-%m-%d %H:%M:%S%z}]',
                    text=get_text(tweet.text, attachments),
                    user=user,
                    source=f"https://twitter.com/{user.alias}/statuses/{tweet.id}",
                    created_at=datetime.timestamp(tweet.created_at),
                    images=[x.url for x in attachments if x.attachment_type == 'image'],
                    hashtags=get_hashtags(tweet.text)
                )
            )

        return tweets_data
