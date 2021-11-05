from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import (get_object_or_404, redirect, render)

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, settings.POSTSNUM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title': 'Последние обновления на сайте',
        'page_obj': page_obj}

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_in_group = group.posts.all()
    paginator = Paginator(posts_in_group, settings.POSTSNUM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title': group.title,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    following = False
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    posts_count = len(posts)
    paginator = Paginator(posts, settings.POSTSNUM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if (request.user.is_authenticated and request.user.follower.
            filter(author=author).exists()):
        following = True

    context = {
        'title': f'Профайл пользователя {author}',
        'page_obj': page_obj,
        'author': author,
        'following': following,
        'posts_count': posts_count,
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)

    context = {
        'title': 'Добавить запись',
        'form': form}

    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)

    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'form': form,
        'title': 'Редактировать запись',
        'is_edit': True}

    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    followed_authors = request.user.follower.values('author')
    posts = Post.objects.filter(author__in=followed_authors)
    paginator = Paginator(posts, settings.POSTSNUM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Ваши подписки'
    context = {
        'title': title,
        'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if (request.user != author and not
            request.user.follower.filter(author=author).exists()):
        Follow.objects.create(author=author, user=request.user)
        return redirect('posts:profile', username)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following = request.user.follower.filter(author=author)
    following.delete()
    return redirect('posts:profile', username)
