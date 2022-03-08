from typing import List

from pydantic import BaseModel
from tweepy import Response





class Attachment(BaseModel):
    attachment_type: str
    url: str
    text: str

    @staticmethod
    def from_response(response: Response, data, tweet_quotes) -> List["Attachment"]:
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
                attachment_text = media.alt_text if media.alt_text else "media"
                attachments.append(Attachment(attachment_type=media.type, text=attachment_text, url=url))

        if not tweet_quotes or "referenced_tweets" not in data:
            return attachments

        for referenced_tweet in data["referenced_tweets"]:
            attachments.append(
                Attachment(
                    attachment_type=referenced_tweet["type"],
                    text="",
                    url=referenced_tweet["id"],
                )
            )

        return attachments
