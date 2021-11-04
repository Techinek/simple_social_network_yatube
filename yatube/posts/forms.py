from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        required = ('text',)
        labels = {
            'text': 'Текст',
            'group': 'Группа'
        }
        help_texts = {
            'text': 'Добавьте содержимое поста',
            'group': 'Укажите группу, к которой относится пост',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = 'text',
        required = ('text',)
        labels = {
            'text': 'Комментарий'
        }
        help_text = {
            'text': 'Добавьте комментарий'
        }
