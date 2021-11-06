import shutil
import tempfile
import time

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import Client, TestCase, override_settings
from django.urls import reverse


from ..models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPageTemplates(TestCase):
    """Tests for templates and contexts """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('someuser')
        cls.follower = User.objects.create_user('follower')
        cls.no_follower = User.objects.create_user('no_follower')

        for group_num in range(2):
            Group.objects.create(title=f'Группа № {group_num}',
                                 slug=f'group{group_num}',
                                 description=f'Описание группы №{group_num}')

        for post_num in range(40):
            if post_num % 2 == 0:
                Post.objects.create(text=f'Текст №{post_num}',
                                    author=cls.user,
                                    group=Group.objects.first())
            else:
                Post.objects.create(text=f'Текст №{post_num}',
                                    author=cls.user,
                                    group=Group.objects.last())

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(TestPageTemplates.user)
        self.follower_client = Client()
        self.follower_client.force_login(TestPageTemplates.follower)
        self.no_follower_client = Client()
        self.no_follower_client.force_login(TestPageTemplates.no_follower)

        self.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        self.posts = Post.objects.all()
        self.groups = Group.objects.all()
        self.first_post = Post.objects.last()
        self.first_group = Group.objects.last()
        self.last_group = Group.objects.first()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_urls_having_correct_templates(self):
        urls_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:posts_in_group',
                    args=(self.first_group.slug,)): 'posts/group_list.html',
            reverse('posts:profile',
                    args=(self.user,)): 'posts/profile.html',
            reverse('posts:post_detail',
                    args=(self.first_post.pk,)): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    args=(self.first_post.pk,)): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'}
        for reversed_url, template in urls_templates.items():
            with self.subTest(reversed_url=reversed_url):
                response = self.authorized_client.get(reversed_url)
                self.assertTemplateUsed(response, template)

    def test_index_group_profile_pages_and_contexts(self):
        filtered_posts = self.posts.filter(group=self.first_group)
        profile_posts = self.posts.filter(author=self.user)
        urls_contexts = {
            reverse('posts:index'): self.posts[:10],
            reverse('posts:posts_in_group',
                    args=(self.first_group.slug,)): filtered_posts[:10],
            reverse('posts:profile',
                    args=(self.user,)): profile_posts[:10],
        }

        for url, context in urls_contexts.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.context['page_obj'].object_list,
                                 list(context))

    def test_first_page_contains_ten_records(self):
        urls = (
            reverse('posts:index'),
            reverse('posts:posts_in_group', args=(self.first_group.slug,)),
            reverse('posts:profile', args=(self.user,)))

        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POSTSNUM)

    def test_second_page_contains_ten_records(self):
        urls = (
            reverse('posts:index'),
            reverse('posts:posts_in_group', args=(self.first_group.slug,)),
            reverse('posts:profile',
                    args=(self.user,)))

        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POSTSNUM)

    def test_post_detail_with_context(self):
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              args=(self.first_post.pk,)))

        self.assertEqual(response.context.get('post').pk, self.first_post.pk)
        self.assertEqual(response.context.get('post').text,
                         self.first_post.text)
        self.assertEqual(response.context.get('post').author,
                         self.first_post.author)

    def test_create_post_form(self):
        response = self.authorized_client.get(reverse('posts:post_create'))

        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_form(self):
        response = self.authorized_client.get(reverse(
                                              'posts:post_edit',
                                              args=(self.first_post.pk,)))

        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_sequence_render(self):
        new_post = Post.objects.create(text='Проверка поста',
                                       author=self.user,
                                       group=self.last_group)

        urls_rendering_new_post = (
            reverse('posts:index'),
            reverse('posts:posts_in_group',
                    args=(self.last_group.slug,)),
            reverse('posts:profile',
                    args=(self.user,)))

        for url in urls_rendering_new_post:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertContains(response, new_post)

        # check that new_post was not rendered on other group

        group_path = reverse('posts:posts_in_group',
                             args=(self.first_group.slug,))
        response = self.authorized_client.get(group_path)
        self.assertNotContains(response, new_post)

    def test_image_passed_in_post_context(self):
        self.post_group = Group.objects.first()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')

        post_with_image = Post.objects.create(
            text='Текст с картинкой',
            image=uploaded,
            author=self.user,
            group=self.post_group)

        urls = (
            reverse('posts:index'),
            reverse('posts:profile', args=(self.user,)),
            reverse('posts:posts_in_group', args=(self.post_group.slug,)),
        )

        last_post = Post.objects.order_by('-pk')[0]
        default_upload_path = last_post._meta.get_field('image').upload_to
        path_to_file = f"{default_upload_path}{uploaded.name}"

        response = self.client.get(reverse('posts:post_detail',
                                           args=(post_with_image.pk,)))

        # check that image is rendered on post detail

        self.assertEqual(response.context['post'].image.name,
                         path_to_file)

        # check that image is rendered on listing pages

        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.context['page_obj'][0].image.name,
                                 path_to_file)

    def test_index_page_cache(self):
        settings.DEBUG = True

        self.client.get(reverse('posts:index'))
        num_of_db_connections_after_first_request = len(connection.queries)

        self.client.get(reverse('posts:index'))
        num_of_db_connections_after_second_request = len(connection.queries)

        self.assertGreater(num_of_db_connections_after_first_request,
                           num_of_db_connections_after_second_request)

        # waiting to drop the cache

        time.sleep(20)

        self.client.get(reverse('posts:index'))
        num_of_db_connections_with_cache_reset = len(connection.queries)

        self.assertEqual(num_of_db_connections_after_first_request,
                         num_of_db_connections_with_cache_reset)

    def test_followers_subscription(self):
        response = self.follower_client.get(reverse('posts:follow_index'))

        # check that on follow_index page there are no posts by default

        self.assertEqual(len(response.context['page_obj']), 0)

        self.follower_client.get(reverse('posts:profile_follow',
                                         args=(self.user,)))

        # check that after subscribing posts are added on follow_page

        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertGreater(len(response.context['page_obj']), 0)

    def test_unsubscribe_from_author(self):
        self.follower_client.get(reverse('posts:profile_follow',
                                         args=(self.user,)))
        self.follower_client.get(reverse('posts:profile_unfollow',
                                         args=(self.user,)))

        # check that after unsubscribing posts are removed from follow_page
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_new_post_appearing_in_subscriber_rss(self):
        self.follower_client.get(reverse('posts:profile_follow',
                                         args=(self.user,)))
        Post.objects.create(text='Последний пост', author=self.user)
        last_post = Post.objects.order_by('-pk')[0]

        # check that new post appeared on subscriber's page

        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertContains(response, last_post)

        # check that user who is not subscribed has no last post on the page

        response = self.no_follower_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, last_post)
