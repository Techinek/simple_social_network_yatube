import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('someuser')
        cls.post = Post.objects.create(text='Тестовый пост', author=cls.user)
        cls.group = Group.objects.create(title='Группа', slug='group')

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(PostCreateFormTests.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_creation(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Пост через POST',
        }
        response = self.auth_client.post(reverse('posts:post_create'),
                                         data=form_data, follow=True)
        self.assertRedirects(response,
                             reverse('posts:profile', args=(self.user,)))
        last_post = Post.objects.order_by('-pk')[0]
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(last_post.text == form_data['text'])

    def test_post_creation_with_group(self):
        posts_count = Post.objects.count()
        form_data_with_group = {
            'text': 'Пост c группой через POST',
            'group': self.group.pk,
        }
        self.auth_client.post(reverse('posts:post_create'),
                              data=form_data_with_group,
                              follow=True)
        last_post = Post.objects.order_by('-pk')[0]
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(last_post.text == form_data_with_group['text'])
        self.assertTrue(last_post.group.pk == form_data_with_group['group'])

    def test_posting_and_editing_by_anonymous_user(self):
        restricted_urls = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=(self.post.pk,)),
        )
        for url in restricted_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTrue(response, HTTPStatus.TEMPORARY_REDIRECT)

    def test_post_edit(self):
        form_data = {
            'text': 'Пост обновлен',
        }
        self.auth_client.post(reverse('posts:post_edit',
                              args=(self.post.pk,)),
                              data=form_data, follow=True)
        edited_post = Post.objects.get(id=self.post.pk)
        self.assertNotEqual(self.post.text, edited_post.text)

    def test_post_with_image_created_in_db(self):
        posts_count = Post.objects.count()
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

        form_data = {
            'text': 'Текст поста',
            'image': uploaded}

        self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)

        last_post = Post.objects.order_by('-pk')[0]
        self.assertEqual(Post.objects.count(), posts_count + 1)

        # check that last post contains image from form_data

        default_upload_path = last_post._meta.get_field('image').upload_to
        path_to_file = f"{default_upload_path}{uploaded.name}"
        self.assertEqual(last_post.image, path_to_file)

    def test_comment_creation_by_unknown_user(self):
        post_comments_count = self.post.comments.count()
        form_data = {
            'text': 'Текст комментария',
            'post': self.post.pk,
            'author': self.user
        }

        # check that authorized client can publish a comment

        self.auth_client.post(
                reverse('posts:add_comment', args=(self.post.pk,)),
                data=form_data,
                follow=True
        )
        self.assertEqual(self.post.comments.count(), post_comments_count + 1)

        # check that comment is published

        response = self.client.get(reverse('posts:post_detail',
                                           args=(self.post.pk,)))

        self.assertEqual(response.context['comments'][0],
                         self.post.comments.last())
