from typing import List

import tweepy
from tweepy import Response

from ServiceConfig import ServiceConfig

SERVICE_CONFIG = ServiceConfig()


class Attachment:
    def __init__(self, attachment_type: str, text: str, url: str):
        self.attachment_type = attachment_type
        self.text = text
        self.url = url

    @staticmethod
    def from_response(response: Response, data) -> List["Attachment"]:
        if "media" in response.includes:
            media_dict = {m["media_key"]: m for m in response.includes["media"]}
        else:
            media_dict = dict()

        media_keys = list()
        if "attachments" in data:
            media_keys.extend(data["attachments"]["media_keys"])

        attachments = list()
        for index, media_key in enumerate(media_keys):
            media = media_dict[media_key]
            if media:
                url = media.url if media.url else media.preview_image_url
                if media.type == "video":
                    url = f"https://twitter.com/user/statuses/{data['id']}/video/1"
                attachments.append(Attachment(media.type, media.alt_text, url))

        if "referenced_tweets" not in data:
            return attachments

        client = tweepy.Client(SERVICE_CONFIG.twitter_bearer_token)

        for referenced_tweet in data["referenced_tweets"]:
            referenced_tweet_response = client.get_tweet(id=referenced_tweet["id"])
            attachments.append(
                Attachment(
                    referenced_tweet["type"],
                    referenced_tweet_response.data.text,
                    f"https://twitter.com/user/statuses/{referenced_tweet_response.data.id}",
                )
            )

        return attachments
