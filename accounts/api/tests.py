from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User


LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'


class AccountApiTests(TestCase):

    def setUp(self):
        # this function is executed when the 'test function' command is triggered
        self.client = APIClient()
        self.user = self.create_user(
            username='admin',
            email='test@test.com',
            password='correct password',
        )

    def create_user(self, username, email, password):
        return User.objects.create_user(username, email, password)

    def test_login(self):
        # test1: method is supposed to be POST
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        # login failure: return status code 405 = METHOD_NOT_ALLOWED
        self.assertEqual(response.status_code, 405)

        # test2: password wrong
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password',
        })
        self.assertEqual(response.status_code, 400)

        # test3: correct password
        # verify no user is logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)
        # verify logging in with correct password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['email'], 'test@test.com')
        # verify login status after logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        # login before testing
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        # verify the user is successfully logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # test1: method is supposed to be post
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # test2: change method to post request
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)
        # verify the user has logged out successfully
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@test.com',
            'password': 'any password',
        }
        # test1: method is supposed to be post
        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        # test2: incorrect email
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'incorrect email',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)

        # test3: password too short
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@test.com',
            'password': '123',
        })
        self.assertEqual(response.status_code, 400)

        # test4: username too long
        response = self.client.post(SIGNUP_URL, {
            'username': 'username is tooooooooooooooooo loooooooong',
            'email': 'someone@test.com',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)

        # test5: successful registration
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')
        # verify the newly registered user has logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)