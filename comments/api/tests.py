from testing.testcases import TestCase
from rest_framework.test import APIClient
from comments.models import Comment
from django.utils import timezone


COMMENT_URL = '/api/comments/'
COMMENT_DETAIL_URL = '/api/comments/{}/'

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

    def test_destroy(self):
        comment = self.create_comment(self.alfredo, self.tweet)
        url = COMMENT_DETAIL_URL.format(comment.id)
        # cannot delete by anonymous user
        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # only author can delete
        response = self.trump_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # author can delete
        count = Comment.objects.count()
        response = self.alfredo_client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), count - 1)

    def test_update(self):
        comment = self.create_comment(self.alfredo, self.tweet, 'original')
        another_tweet = self.create_tweet(self.trump)
        url = COMMENT_DETAIL_URL.format(comment.id)

        # when we use put
        # cannot update by anonymous user
        response = self.anonymous_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)
        # only author can update
        response = self.trump_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'new')
        # cannot update anything other than contents, but only silent process exceptions
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.alfredo_client.put(url, {
            'content': 'new',
            'user_id': self.trump.id,
            'tweet_id': another_tweet.id,
            'created_at': now,
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'new')
        self.assertEqual(comment.user, self.alfredo)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertNotEqual(comment.updated_at, before_updated_at)

    def test_list(self):
        # tweet_id required
        response = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # can access with tweet_id
        # no comment initially
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        # sorted by comment time
        self.create_comment(self.alfredo, self.tweet, '1')
        self.create_comment(self.trump, self.tweet, '2')
        self.create_comment(self.trump, self.create_tweet(self.trump), '3')
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')

        # provide user_id & tweet_id: only tweet_id will be filtered
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'user_id': self.alfredo.id,
        })
        self.assertEqual(len(response.data['comments']), 2)