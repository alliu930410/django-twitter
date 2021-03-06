from django.contrib.auth.models import User
from django.test import TestCase
from tweets.models import Tweet
from utils.time_helpers import utc_now
from datetime import timedelta


class TweetTests(TestCase):

    def test_hours_to_now(self):
        hippo = User.objects.create_user(username='hippo')
        tweet = Tweet.objects.create(user=hippo, content='Mr Hippo Posted a Tweet!')
        tweet.created_at = utc_now() - timedelta(hours=10)
        tweet.save()
        self.assertEqual(tweet.hours_to_now, 10)
