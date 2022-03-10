from typing import List, Dict, Any, Set

import tweepy
from pydantic import BaseModel
from tweepy import Response

from ServiceConfig import ServiceConfig
from data.Attachment import Attachment
from data.User import User
from datetime import datetime

import re

SERVICE_CONFIG = ServiceConfig()


class TweetData(BaseModel):
    created_at: int
    user: User
    text: str
    images_urls: List[str]
    source: str
    hashtags: List[str]
    title: str

    @staticmethod
    def from_tweets_list(response: Response, query: str, tweet_quotes=True) -> List["TweetData"]:
        if not response.data:
            return []

        tweets_data = list()

        for data in response.data:
            user = User.from_response(response, data.author_id)
            attachments = Attachment.from_response(response, data.data, tweet_quotes)
            if "urls" in data.entities and data.entities["urls"] and len(data.entities["urls"]):
                expanded_urls = {x["url"]: x["expanded_url"] for x in data.entities["urls"]}
            else:
                expanded_urls = {}

            tweets_data.append(
                TweetData(
                    title=f"{user.display_name} [{data.created_at:%Y-%m-%d %H:%M:%S}]",
                    text=get_text(data.text, attachments, expanded_urls),
                    user=user,
                    source=f"https://twitter.com/{user.alias}/statuses/{data.id}",
                    created_at=datetime.timestamp(data.created_at),
                    images_urls=[x.url for x in attachments if x.attachment_type == "photo"],
                    hashtags=get_hashtags(data.text).union({query}) if query else get_hashtags(data.text)
                )
            )

        return tweets_data

    @staticmethod
    def from_id(tweet_id: str) -> "TweetData":
        client = tweepy.Client(SERVICE_CONFIG.twitter_bearer_token)
        response = client.get_tweets(
            ids=[tweet_id],
            tweet_fields=["created_at", "referenced_tweets", "entities"],
            media_fields=["url", "alt_text", "preview_image_url"],
            expansions=["attachments.media_keys", "author_id"],
        )
        return TweetData.from_tweets_list(response, '', False)[0]


def get_text(text: str, attachments: List[Attachment], expanded_urls: Dict[str, str]):
    for url, expanded_url in expanded_urls.items():
        text = text.replace(url, expanded_url)

    hashtags = get_hashtags(text)
    links = get_links(text)

    text = replace_hashtags(hashtags, text)
    text = replace_links(links, text)
    text = text + "\n\n".join([f"![{x.text}]({x.url})" for x in attachments if x.attachment_type == "photo"])

    tweet_data_references = [TweetData.from_id(x.url) for x in attachments if x.attachment_type == "quoted"]
    for tweet_data_reference in tweet_data_references:
        text = text + "\n\nQuoted tweet:\n\n" + tweet_data_reference.title + "\n\n" + tweet_data_reference.text
    return text


def replace_links(links, text):
    for link in links:
        start_character_matches = sorted([m.start() for m in re.finditer(link, text)], reverse=True)
        for start in start_character_matches:
            try:
                next_character = text[start + len(link)]
                if next_character == " " or next_character == "\t" or next_character == "\n":
                    text = text[:start] + f"[{link}]({link})" + text[start + len(link) :]
            except IndexError:
                text = text[:start] + f"[{link}]({link})"
    return text


def replace_hashtags(hashtags: Set[str], text: str):
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
    return text


def get_hashtags(text: str) -> Set[str]:
    return set(re.findall(r"(#\w+)", text))


def get_links(text: str) -> Set[str]:
    return set([t for t in text.split() if t.startswith("https://")])
