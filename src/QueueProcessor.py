from datetime import datetime, timezone
from time import sleep
from typing import List

import pymongo as pymongo
import redis
import requests
import tweepy
from pydantic import ValidationError
from rsmq.consumer import RedisSMQConsumer
from rsmq import RedisSMQ

from ServiceConfig import ServiceConfig
from data.Task import Task
from data.TweetData import TweetData
from data.TweetMessage import TweetMessage

class UserSuspended(Exception):
    pass

class QueueProcessor:

    TIME_BETWEEN_QUERIES_IN_MINUTES = 4

    def __init__(self):
        self.service_config = ServiceConfig()
        self.logger = self.service_config.get_logger("redis_tasks")
        client = pymongo.MongoClient(f"mongodb://{self.service_config.mongo_host}:{self.service_config.mongo_port}")
        self.tweets_db = client["tweets"]

        self.results_queue = RedisSMQ(
            host=self.service_config.redis_host,
            port=self.service_config.redis_port,
            qname=self.service_config.results_queue_name,
        )

    def process(self, id, message, rc, ts):
        try:
            task = Task(**message)

            if self.last_query_was_too_recent(task):
                self.logger.info(f"Skipped message: {message}")
                return True

            self.logger.info(f"Valid message: {message}")

            tweets_data: List[TweetData] = self.get_tweets(task)

            self.logger.info(f"output messages for {task.params.query}: {len(tweets_data)}")

            for tweet_data in tweets_data:
                tweet_message = TweetMessage(tenant=task.tenant, task=task.task, params=tweet_data, success=True)
                self.results_queue.sendMessage(delay=3).message(tweet_message.dict()).execute()
                sleep(1)

        except ValidationError:
            self.logger.error(f"Not a valid message: {message}")
        except requests.exceptions.ConnectionError:
            self.logger.info(f"ConnectionError: {message}")
        except tweepy.errors.BadRequest:
            self.logger.info(f"Not a valid user: {message}")
        except tweepy.errors.HTTPException:
            self.logger.info(f"Twitter api not available: {message}")
        except UserSuspended:
            self.logger.info(f"User suspended: {message}")
        except Exception:
            self.logger.error("error getting the tweets", exc_info=1)

        return True

    def get_tweets(self, task: Task):
        tweepy_client = tweepy.Client(self.service_config.twitter_bearer_token)
        tweepy_params = self.get_tweepy_query_params(task)

        if task.params.query[0] == "@":
            tweepy_tweets = tweepy_client.get_users_tweets(**tweepy_params)
        else:
            tweepy_tweets = tweepy_client.search_recent_tweets(**tweepy_params)

        tweets_data = TweetData.from_tweets_list(tweepy_tweets, self.get_sanitized_query(task.params.query))

        self.save_tweet_query_in_db(task, tweets_data)

        return tweets_data

    def get_tweepy_query_params(self, task):
        tweepy_params = {
            "max_results": 10,
            "tweet_fields": ["created_at", "referenced_tweets", "entities"],
            "media_fields": ["url", "alt_text", "preview_image_url"],
            "expansions": ["attachments.media_keys", "author_id"],
        }

        tweet_data = self.tweets_db.tweets.find_one({"tenant": task.tenant, "query": task.params.query})
        if tweet_data:
            tweepy_params["since_id"] = tweet_data["last_id_inserted"]

        if task.params.query[0] == "@":
            tweepy_client = tweepy.Client(self.service_config.twitter_bearer_token)
            user = tweepy_client.get_user(username=task.params.query[1:])
            if user.errors and 'detail' in user.errors[0] and 'suspended' in user.errors[0]['detail']:
                raise UserSuspended

            tweepy_params["id"] = user.data["id"]
        else:
            tweepy_params["query"] = f"{self.get_sanitized_query(task.params.query)} -is:reply -is:retweet"

        return tweepy_params

    def last_query_was_too_recent(self, task: Task):
        tweet_data = self.tweets_db.tweets.find_one({"tenant": task.tenant, "query": task.params.query})

        if not tweet_data:
            return False

        timestamp_now = int(datetime.now(tz=timezone.utc).timestamp())
        last_query_timestamp = tweet_data["last_query_timestamp"]

        return timestamp_now - QueueProcessor.TIME_BETWEEN_QUERIES_IN_MINUTES * 60 < last_query_timestamp

    def save_tweet_query_in_db(self, task, tweets_data):
        if not len(tweets_data):
            return

        last_id_inserted = max([x.tweet_id for x in tweets_data])
        self.tweets_db.tweets.delete_many({"tenant": task.tenant, "query": task.params.query})
        self.tweets_db.tweets.insert_one(
            {
                "tenant": task.tenant,
                "query": task.params.query,
                "last_query_timestamp": int(datetime.now(tz=timezone.utc).timestamp()),
                "last_id_inserted": last_id_inserted,
            }
        )

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

    @staticmethod
    def get_sanitized_query(query):
        if "search#" == query[:7]:
            return query[7:]

        return query


if __name__ == "__main__":
    redis_tasks_processor = QueueProcessor()
    redis_tasks_processor.subscribe_to_extractions_tasks_queue()
