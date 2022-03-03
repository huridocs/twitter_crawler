from unittest import TestCase

from data.TweetData import get_hashtags


class TestTweetData(TestCase):
    def test_regex(self):
        self.assertEqual([], get_hashtags('no hashtags'))
        self.assertEqual(['#one'], get_hashtags('no hashtags #one'))
        self.assertEqual(['#one', '#two'], get_hashtags('no hashtags #one #two'))
        self.assertEqual(['#one', '#two'], get_hashtags('#one no hashtags  #two'))
        self.assertEqual(['#one', '#two'], get_hashtags('#one.no hashtags  #two'))
        self.assertEqual(['#one', '#two'], get_hashtags('#one,no hashtags  #two'))
        self.assertEqual(['#one', '#no', '#two'], get_hashtags('#one#no hashtags  #two'))