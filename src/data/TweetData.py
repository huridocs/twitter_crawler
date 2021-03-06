from typing import List, Dict, Set

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
    tweet_id: int

    @staticmethod
    def from_tweets_list(response: Response, query: str, tweet_quotes=True) -> List["TweetData"]:
        if not response.data:
            return []

        tweets_data = list()

        for data in response.data:
            user = User.from_response(response, data.author_id)
            attachments = Attachment.from_response(response, data.data, tweet_quotes)
            if data.entities and "urls" in data.entities and data.entities["urls"] and len(data.entities["urls"]):
                expanded_urls = {x["url"]: x["expanded_url"] for x in data.entities["urls"]}
            else:
                expanded_urls = {}

            quoted_tweets = [TweetData.from_id(x.url) for x in attachments if x.attachment_type == "quoted"]
            quoted_images_urls = []
            for quoted_tweet in quoted_tweets:
                quoted_images_urls += quoted_tweet.images_urls

            tweets_data.append(
                TweetData(
                    title=f"{user.display_name} [{data.created_at:%Y-%m-%d %H:%M:%S}]",
                    text=get_text(data.text, attachments, expanded_urls, quoted_tweets),
                    user=user,
                    source=f"https://twitter.com/{user.alias}/statuses/{data.id}",
                    created_at=datetime.timestamp(data.created_at),
                    images_urls=set([x.url for x in attachments if x.attachment_type == "photo"] + quoted_images_urls),
                    hashtags=get_hashtags(data.text).union({query}) if query else get_hashtags(data.text),
                    tweet_id=data.id,
                )
            )

        tweets_data.sort(key=lambda x: x.tweet_id)
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
        return TweetData.from_tweets_list(response, "", False)[0]


def get_text(text: str, attachments: List[Attachment], expanded_urls: Dict[str, str], quoted_tweets=None):
    if quoted_tweets is None:
        quoted_tweets = list()

    for url, expanded_url in expanded_urls.items():
        text = text.replace(url, expanded_url)

    hashtags = get_hashtags(text)
    links = get_links(text)
    users = get_users(text)

    text = replace_hashtags(hashtags, text)
    text = replace_links(links, text)
    text = replace_users(users, text)
    text = text + "\n\n".join([f"![{x.text}]({x.url})" for x in attachments if x.attachment_type == "photo"])

    for quoted_tweet in quoted_tweets:
        text = text + "\n\nQuoted tweet:\n\n" + quoted_tweet.title + "\n\n" + quoted_tweet.text
    return text


def replace_links(links, text):
    for link in links:
        try:
            start_character_matches = sorted([m.start() for m in re.finditer(link, text)], reverse=True)
        except re.error:
            continue
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


def replace_users(users: Set[str], text: str):
    for user in users:
        start_character_matches = sorted([m.start() for m in re.finditer(user, text)], reverse=True)
        for start in start_character_matches:
            try:
                next_character = text[start + len(user)]
                if not next_character.isalnum():
                    text = text[:start] + f"[{user}](https://twitter.com/{user[1:]})" + text[start + len(user) :]
            except IndexError:
                text = text[:start] + f"[{user}](https://twitter.com/{user[1:]})"
    return text


def get_hashtags(text: str) -> Set[str]:
    return set(re.findall(r"(#\w+)", text))


def get_users(text: str) -> Set[str]:
    return set(re.findall(r"(@\w+)", text))


def get_links(text: str) -> Set[str]:
    return set([t for t in text.split() if t.startswith("https://")])
