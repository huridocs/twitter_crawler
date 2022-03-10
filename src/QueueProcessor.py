from datetime import datetime
from time import sleep
from typing import List

import redis
import tweepy
from pydantic import ValidationError
from rsmq.consumer import RedisSMQConsumer
from rsmq import RedisSMQ

from ServiceConfig import ServiceConfig
from data.Task import Task
from data.TweetData import TweetData
from data.TweetMessage import TweetMessage
from timestamp_to_recent_utc import timestamp_to_recent_utc


class QueueProcessor:
    def __init__(self):
        self.service_config = ServiceConfig()
        self.logger = self.service_config.get_logger("redis_tasks")

        self.results_queue = RedisSMQ(
            host=self.service_config.redis_host,
            port=self.service_config.redis_port,
            qname=self.service_config.results_queue_name,
        )

    def process(self, id, message, rc, ts):
        try:
            task = Task(**message)
        except ValidationError:
            self.logger.error(f"Not a valid message: {message}")
            return True

        self.logger.info(f"Valid message: {message}")

        try:
            tweepy_client = tweepy.Client(self.service_config.twitter_bearer_token)
            message_time_threshold = datetime.utcnow().timestamp() - 300

            if ts/1000 < message_time_threshold:
                return True

            shifted_seconds = 120
            window_seconds = 120
            start_time = timestamp_to_recent_utc(ts/1000 - window_seconds - shifted_seconds)
            end_time = timestamp_to_recent_utc(ts/1000 - shifted_seconds)

            tweets_from_ids = tweepy_client.search_recent_tweets(
                f"{task.params.query} -is:reply -is:retweet",
                max_results=10,
                start_time=start_time,
                end_time=end_time,
                tweet_fields=["created_at", "referenced_tweets", "entities"],
                media_fields=["url", "alt_text", "preview_image_url"],
                expansions=["attachments.media_keys", "author_id"],
            )

            tweets_data: List[TweetData] = TweetData.from_tweets_list(tweets_from_ids, task.params.query)
            self.logger.info(f"output messages for {task.params.query}: {len(tweets_data)}")

            for tweet_data in tweets_data:
                tweet_message = TweetMessage(tenant=task.tenant, task=task.task, params=tweet_data, success=True)
                self.results_queue.sendMessage(delay=3).message(tweet_message.dict()).execute()
                sleep(1)

            sleep(5)
            return True

        except Exception:
            self.logger.error("error getting the tweets", exc_info=1)
            return True

    def subscribe_to_extractions_tasks_queue(self):
        while True:
            try:
                self.results_queue.createQueue().vt(120).exceptions(False).execute()
                extractions_tasks_queue = RedisSMQ(
                    host=self.service_config.redis_host,
                    port=self.service_config.redis_port,
                    qname=self.service_config.tasks_queue_name,
                )

                extractions_tasks_queue.createQueue().vt(120).exceptions(False).execute()

                self.logger.info(f"Connecting to redis: {self.service_config.redis_host}:{self.service_config.redis_port}")

                redis_smq_consumer = RedisSMQConsumer(
                    qname=self.service_config.tasks_queue_name,
                    processor=self.process,
                    host=self.service_config.redis_host,
                    port=self.service_config.redis_port,
                )
                redis_smq_consumer.run()
            except redis.exceptions.ConnectionError:
                self.logger.error(
                    f"Error connecting to redis: {self.service_config.redis_host}:{self.service_config.redis_port}"
                )
                sleep(20)


if __name__ == "__main__":
    redis_tasks_processor = QueueProcessor()
    redis_tasks_processor.subscribe_to_extractions_tasks_queue()
