from newsfeeds.models import NewsFeed
from friendships.models import Friendship
from rest_framework.test import APIClient
from testing.testcases import TestCase

NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedApiTest(TestCase):

    def setUp(self):
        self.alfredo = self.create_user('alfredo')
        self.alfredo_client = APIClient()
        self.alfredo_client.force_authenticate(self.alfredo)

        self.trump = self.create_user('trump')
        self.trump_client = APIClient()
        self.trump_client.force_authenticate(self.trump)

        # create followings and follower for alfredo
        for i in range(2):
            follower = self.create_user('alfredo_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.alfredo)
        for i in range(3):
            following = self.create_user('alfredo_following{}'.format(i))
            Friendship.objects.create(from_user=self.alfredo, to_user=following)

    def test_list(self):
        # only authenticated users can see newsfeeds
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)
        # cannot use POST request
        response = self.alfredo_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)
        # the newsfeed should be blank when initialized
        response = self.alfredo_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 0)
        # user can see their own tweets in the newsfeed
        self.alfredo_client.post(POST_TWEETS_URL, {'content': 'I should be able to see this'})
        response = self.alfredo_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 1)
        # user should be able see their followings's posts
        self.alfredo_client.post(FOLLOW_URL.format(self.trump.id))
        response = self.trump_client.post(
            POST_TWEETS_URL,
            {'content': 'Alfredo should be able to see this'},
        )
        posted_tweet_id = response.data['id']
        response = self.alfredo_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)

