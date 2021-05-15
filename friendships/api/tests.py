from friendships.models import Friendship
from rest_framework.test import APIClient
from testing.testcases import TestCase


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTest(TestCase):

    def setUp(self):
        self.anonymous_client = APIClient()

        self.alfredo = self.create_user('alfredo')
        self.alfredo_client = APIClient()
        self.alfredo_client.force_authenticate(self.alfredo)

        self.trump = self.create_user('trump')
        self.trump_client = APIClient()
        self.trump_client.force_authenticate(self.trump)

        # create followings and follower for alfredo
        # alfredo_follower1,alfredo_follower2 will follow alfredo
        # alfredo will follow alfredo_following1,alfredo_following2, alfredo_following
        for i in range(2):
            follower = self.create_user('alfredo_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.alfredo)
        for i in range(3):
            following= self.create_user('alfredo_following{}'.format(i))
            Friendship.objects.create(from_user=self.alfredo, to_user=following)

    def test_follow(self):
        url = FOLLOW_URL.format(self.alfredo.id)

        # request method need to be post
        response = self.trump_client.get(url)
        self.assertEqual(response.status_code, 405)
        # need to be authenticated to follow others
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # cannot follow the authenticated user itself
        response = self.alfredo_client.post(url)
        self.assertEqual(response.status_code, 400)
        # follow success
        response = self.trump_client.post(url)
        self.assertEqual(response.status_code, 201)
        # silence handling of the duplicated follow(success)
        response = self.trump_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['duplicate'], True)
        # reverse follow will create new data
        count = Friendship.objects.count()
        response = self.alfredo_client.post(FOLLOW_URL.format(self.trump.id))
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.alfredo.id)

        # request method needs to be post
        response = self.trump_client.get(url)
        self.assertEqual(response.status_code, 405)
        # only authenticated user can unfollow others
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # cannot unfollow the authenticated user itself
        response = self.alfredo_client.post(url)
        self.assertEqual(response.status_code, 400)
        # unfollow success
        Friendship.objects.create(from_user=self.trump, to_user=self.alfredo)
        count = Friendship.objects.count()
        response = self.trump_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Friendship.objects.count(), count - 1)
        # silence handling of the scenario if trying to unfollow a user
        # that the authenticated user did not follow
        count = Friendship.objects.count()
        response = self.trump_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendship.objects.count(), count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.alfredo.id)

        # post method not allowed
        response = response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get method success
        response = response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 3)
        # the returned object is ordered descending by creation time
        self.assertEqual(
            response.data['followings'][0]['user']['username'],
            'alfredo_following2',
        )
        self.assertEqual(
            response.data['followings'][1]['user']['username'],
            'alfredo_following1',
        )
        self.assertEqual(
            response.data['followings'][2]['user']['username'],
            'alfredo_following0',
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.alfredo.id)

        # post method not allowed
        response = response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get method success
        response = response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 2)
        # the returned object is ordered descending by creation time
        self.assertEqual(
            response.data['followers'][0]['user']['username'],
            'alfredo_follower1',
        )
        self.assertEqual(
            response.data['followers'][1]['user']['username'],
            'alfredo_follower0',
        )