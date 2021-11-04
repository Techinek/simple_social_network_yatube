from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UserUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('some_user')

    def setUp(self):
        self.authenticated_client = Client()
        self.authenticated_client.force_login(UserUrlTests.user)
        self.user_urls = (
            reverse('users:signup'),
            reverse('users:login'),
            reverse('users:password_change'),
            reverse('users:password_change_done'),
            reverse('users:password_reset_form'),
            reverse('users:password_reset_done'),
            reverse('users:password_reset_complete'),
            reverse('users:logout'),
        )

    def test_auth_urls_statuses(self):
        for url in self.user_urls:
            with self.subTest(url=url):
                response = self.authenticated_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_namespaces(self):
        for reversed_url in self.user_urls:
            with self.subTest(reversed_url=reversed_url):
                response = self.authenticated_client.get(reversed_url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
