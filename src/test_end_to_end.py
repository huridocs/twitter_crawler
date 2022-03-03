import json
import subprocess
import time
from unittest import TestCase

from rsmq import RedisSMQ

from data.Params import Params
from data.Task import Task
from data.TweetMessage import TweetMessage


class TestEndToEnd(TestCase):
    def setUp(self):
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
            params=Params(query="2323423424-42a0bc68-75ca-4b25-82ed-50794d32ba20", from_UTC_timestamp=1645657200),
        )

        queue.sendMessage().message(str(no_search_term_task.json())).execute()

        task = Task(
            tenant=tenant,
            task="get-hashtag",
            params=Params(query="#twitter", from_UTC_timestamp=1645657200),
        )

        queue.sendMessage().message(str(task.json())).execute()

        twitter_message = self.get_redis_message()

        self.assertEqual(tenant, twitter_message.tenant)

    @staticmethod
    def get_redis_message() -> TweetMessage:
        queue = RedisSMQ(host="127.0.0.1", port="6379", qname="twitter_crawler_results", quiet=True)

        for i in range(10):
            time.sleep(2)
            message = queue.receiveMessage().exceptions(False).execute()
            if message:
                queue.deleteMessage(id=message["id"]).execute()
                return TweetMessage(**json.loads(message["message"]))
