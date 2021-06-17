from testing.testcases import TestCase
from rest_framework.test import APIClient


COMMENT_URL = '/api/comments/'


class CommentApiTests(TestCase):

    def setUp(self):
        self.alfredo = self.create_user('alfredo')
        self.alfredo_client = APIClient()
        self.alfredo_client.force_authenticate(self.alfredo)

        self.trump = self.create_user('trump')
        self.trump_client = APIClient()
        self.trump_client.force_authenticate(self.trump)

        self.tweet = self.create_tweet(self.alfredo)

    def test_create(self):
        # anonymous user cannot comment
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)

        # cannot comment with blank parameters
        response = self.alfredo_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # cannot comment with tweet_id only
        response = self.alfredo_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 400)

        # cannot comment with content only
        response = self.alfredo_client.post(COMMENT_URL, {'content': '1'})
        self.assertEqual(response.status_code, 400)

        # content cannot exceed 140 characters
        response = self.alfredo_client.post(
            COMMENT_URL,
            {'content': '1' * 141},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content' in response.data['errors'], True)

        # successful comment with tweet_id and content
        response = self.alfredo_client.post(COMMENT_URL,{
            'tweet_id': self.tweet.id,
            'content': '1',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.alfredo.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], '1')
