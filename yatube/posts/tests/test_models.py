from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test_slug',
                                         description='Тестовое описание')
        cls.post = Post.objects.create(author=cls.user,
                                       text='Тестовый пост больше пятнадцати'
                                            ' символов')

    def test_models_have_correct_object_names(self):
        model_names = {
            self.post.text[:15]: self.post.__str__(),
            self.group.title: self.group.__str__(),
        }
        for model, model_instance in model_names.items():
            with self.subTest(model=model):
                self.assertEqual(model, model_instance)

    def test_verbose_names(self):
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }

        for field, value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(self.post._meta.get_field(field).verbose_name,
                                 value)

    def test_help_texts(self):
        post = PostModelTest.post

        fields_with_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }

        for field, help_text in fields_with_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(post._meta.get_field(field).help_text,
                                 help_text)
