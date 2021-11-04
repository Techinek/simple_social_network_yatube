from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):

    def test_static_pages(self):
        url_status_codes = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse('about:author'): HTTPStatus.OK,
            reverse('about:tech'): HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }

        for url, status_code in url_status_codes.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status_code)


class UrlTemplateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('author_user')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test_group',
                                         description='Описание группы')
        cls.post = Post.objects.create(author=cls.user,
                                       text='Тестовый пост',
                                       group=cls.group)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(UrlTemplateTests.user)

    def test_url_matching_templates(self):
        urls_and_templates = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

        for url, template in urls_and_templates.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
