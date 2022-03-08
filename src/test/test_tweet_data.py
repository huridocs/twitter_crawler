from unittest import TestCase

from data.TweetData import get_hashtags, get_links, get_text


class TestTweetData(TestCase):
    def test_hashtag_regex(self):
        self.assertEqual(set(), get_hashtags("no hashtags"))
        self.assertEqual({"#one"}, get_hashtags("no hashtags #one"))
        self.assertEqual({"#one", "#two"}, get_hashtags("no hashtags #one #two"))
        self.assertEqual({"#one", "#two"}, get_hashtags("#one no hashtags  #two"))
        self.assertEqual({"#one", "#two"}, get_hashtags("#one.no hashtags  #two"))
        self.assertEqual({"#one", "#two"}, get_hashtags("#one,no hashtags  #two"))
        self.assertEqual({"#no", "#one", "#two"}, get_hashtags("#one#no hashtags  #two"))
        self.assertEqual({"#one", "#onetwo"}, get_hashtags("#one#onetwo"))

    def test_link_regex(self):
        self.assertEqual(set(), get_links("no links"))
        self.assertEqual(
            {"https://huridocs.org/wp-content/uploads/2022/02/EN-Uwazi-Demo-16-February-2022.pdf"},
            get_links("💻Join https://huridocs.org/wp-content/uploads/2022/02/EN-Uwazi-Demo-16-February-2022.pdf"),
        )
        self.assertEqual(
            {"https://t.co/DuDcVHK3qp"},
            get_links("Zeya Tun was. #2022Mar4Coup #WhatsHappeningInMyanmar https://t.co/DuDcVHK3qp"),
        )

    def test_get_text(self):
        self.assertEqual("text", get_text("text", [], {}))
        self.assertEqual("text [#one](https://twitter.com/search?q=%23one)", get_text("text #one", [], {}))
        self.assertEqual(
            "text [#one](https://twitter.com/search?q=%23one)[#onetwo](https://twitter.com/search?q=%23onetwo)",
            get_text("text #one#onetwo", [], {}),
        )
        self.assertEqual(
            "text [#one1](https://twitter.com/search?q=%23one1) [#one](https://twitter.com/search?q=%23one)",
            get_text("text #one1 #one", [], {}),
        )
        self.assertEqual(
            "[#one](https://twitter.com/search?q=%23one) text [#onetwo](https://twitter.com/search?q=%23onetwo)",
            get_text("#one text #onetwo", [], {}),
        )
        self.assertEqual(
            "[#one](https://twitter.com/search?q=%23one) [#one](https://twitter.com/search?q=%23one) text",
            get_text("#one #one text", [], {}),
        )
        self.assertEqual(
            "[https://123.is](https://123.is) text",
            get_text("https://123.is text", [], {}),
        )
        self.assertEqual(
            "text [https://123.is](https://123.is)",
            get_text("text https://123.is", [], {}),
        )
        self.assertEqual(
            "text [https://123.is](https://123.is) [https://1234.is](https://1234.is)",
            get_text("text https://123.is https://1234.is", [], {}),
        )
        self.assertEqual(
            "[https://123.is](https://123.is) [https://123.is/1](https://123.is/1)",
            get_text("https://123.is https://123.is/1", [], {}),
        )

    def test_get_text_extended_urls(self):
        self.assertEqual(
            "[https://123.is](https://123.is) text",
            get_text("https://test.is text", [], {'https://test.is': 'https://123.is'}),
        )

