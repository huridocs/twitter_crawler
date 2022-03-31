import json
import subprocess
import time
from unittest import TestCase

import pymongo
from rsmq import RedisSMQ

from ServiceConfig import ServiceConfig
from data.Params import Params
from data.Task import Task
from data.TweetMessage import TweetMessage


class TestEndToEnd(TestCase):
    def setUp(self):
        subprocess.run("../run remove_docker_containers", shell=True)
        subprocess.run("../run start:testing -d", shell=True)
        time.sleep(5)

    def tearDown(self):
        subprocess.run("../run stop", shell=True)

    def test_end_to_end(self):
        tenant = "end_to_end_test"

        queue = RedisSMQ(host="127.0.0.1", port="6379", qname="twitter_crawler_tasks")

        queue.sendMessage().message('{"message_to_avoid":"to_be_written_in_log_file"}').execute()

        no_search_term_task = Task(
            tenant=tenant,
            task="get-hashtag",
            params=Params(
                query="2323423424-42a0bc68-75ca-4b25-82ed-50794d32ba20",
                tweets_languages=["en"],
            ),
        )

        queue.sendMessage().message(str(no_search_term_task.json())).execute()

        no_user_task = Task(
            tenant=tenant,
            task="get-hashtag",
            params=Params(
                query="@no_usr_325792857_32958794857",
                tweets_languages=["en"],
            ),
        )

        queue.sendMessage().message(str(no_user_task.json())).execute()

        service_config = ServiceConfig()
        client = pymongo.MongoClient(f"mongodb://{service_config.mongo_host}:{service_config.mongo_port}")
        tweets_db = client["tweets"]
        tweets_db.tweets.delete_many({"tenant": tenant, "query": "#twitter"})

        task = Task(
            tenant=tenant,
            task="get-hashtag",
            params=Params(query="#twitter", tweets_languages=["en"]),
        )

        queue.sendMessage().message(str(task.json())).execute()

        twitter_message = self.get_redis_message()

        self.assertEqual(tenant, twitter_message.tenant)

        other_message = self.get_redis_message()
        self.assertTrue(twitter_message.params.tweet_id < other_message.params.tweet_id)

    @staticmethod
    def get_redis_message() -> TweetMessage:
        queue = RedisSMQ(host="127.0.0.1", port="6379", qname="twitter_crawler_results", quiet=True)

        for i in range(10):
            time.sleep(2)
            message = queue.receiveMessage().exceptions(False).execute()
            if message:
                queue.deleteMessage(id=message["id"]).execute()
                return TweetMessage(**json.loads(message["message"]))
