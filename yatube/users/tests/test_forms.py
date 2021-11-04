from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserCreationFormsTest(TestCase):
    def test_user_registration(self):
        form_data = {
            'first_name': 'andrey_test',
            'last_name': 'kuskov_test',
            'username': 'andreykus_test',
            'email': 'andrey@test.ru',
            'password1': '1Qdfj0fjglkj8!!',
            'password2': '1Qdfj0fjglkj8!!',
        }

        self.client.post(reverse('users:signup'), data=form_data, follow=True)
        self.assertTrue(User.objects.count())
