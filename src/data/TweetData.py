from typing import List

from pydantic import BaseModel
from tweepy import Response

from data.Attachment import Attachment
from data.User import User
from datetime import datetime

import re


def get_text(text: str, attachments: List[Attachment]):
    hashtags = get_hashtags(text)
    links = get_links(text)

    for hashtag in hashtags:
        start_character_matches = sorted([m.start() for m in re.finditer(hashtag, text)], reverse=True)
        for start in start_character_matches:
            try:
                next_character = text[start + len(hashtag)]
                if not next_character.isalnum():
                    text = (
                        text[:start]
                        + f"[{hashtag}](https://twitter.com/search?q=%23{hashtag[1:]})"
                        + text[start + len(hashtag) :]
                    )
            except IndexError:
                text = text[:start] + f"[{hashtag}](https://twitter.com/search?q=%23{hashtag[1:]})"

    for link in links:
        start_character_matches = sorted([m.start() for m in re.finditer(link, text)], reverse=True)
        for start in start_character_matches:
            try:
                next_character = text[start + len(link)]
                if next_character == " " or next_character == "\t" or next_character == "\n":
                    text = text[:start] + f"[{link}]({link})" + text[start + len(link) :]
            except IndexError:
                text = text[:start] + f"[{link}]({link})"

    text = text + "\n\n".join([f"![{x.text}]({x.url})" for x in attachments if x.attachment_type == "photo"])

    return text


def get_hashtags(text: str):
    return re.findall(r"(#\w+)", text)


def get_links(text: str):
    return [t for t in text.split() if t.startswith("https://")]


class TweetData(BaseModel):
    created_at: int
    user: User
    text: str
    images_urls: List[str]
    source: str
    hashtags: List[str]
    title: str

    @staticmethod
    def from_tweets_list(response: Response) -> List["TweetData"]:
        if not response.data:
            return []

        tweets_data = list()

        for tweet in response.data:
            user = User.from_response(response, tweet.author_id)
            attachments = Attachment.from_response(response, tweet.data)
            tweets_data.append(
                TweetData(
                    title=f"{user.display_name} [{tweet.created_at:%Y-%m-%d %H:%M:%S}]",
                    text=get_text(tweet.text, attachments),
                    user=user,
                    source=f"https://twitter.com/{user.alias}/statuses/{tweet.id}",
                    created_at=datetime.timestamp(tweet.created_at),
                    images_urls=[x.url for x in attachments if x.attachment_type == "photo"],
                    hashtags=get_hashtags(tweet.text),
                )
            )

        return tweets_data
