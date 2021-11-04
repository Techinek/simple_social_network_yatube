from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse


class TestPageResponses(TestCase):
    def setUp(self):
        self.about_urls = {
            reverse('about:tech'): HTTPStatus.OK,
            reverse('about:author'): HTTPStatus.OK,
        }

    def test_url_statuses(self):
        for url in self.about_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_namespaces(self):
        for url in self.about_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
