# news/tests/test_content.py
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from news.forms import CommentForm
from news.models import Comment, News

User = get_user_model()


class TestContent(TestCase):
    """Контент главной и страницы новости (план в readme.txt)."""

    @classmethod
    def setUpTestData(cls):
        # 11 новостей с разными датами: лимит на главной и порядок по дате.
        today = timezone.now().date()
        cls.news_list = [
            News.objects.create(
                title=f'Новость {i}',
                text='Просто текст.',
                date=today - timedelta(days=i),
            )
            for i in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
        ]
        cls.news = cls.news_list[0]
        cls.detail_url = reverse('news:detail', args=(cls.news.pk,))
        cls.author = User.objects.create(username='Комментатор')
        cls.home_url = reverse('news:home')

        now = timezone.now()
        for index in range(10):
            comment = Comment.objects.create(
                news=cls.news,
                author=cls.author,
                text=f'Текст {index}',
            )
            comment.created = now + timedelta(days=index)
            comment.save(update_fields=('created',))

    def test_news_count(self):
        response = self.client.get(self.home_url)
        object_list = response.context['object_list']
        self.assertEqual(len(object_list), settings.NEWS_COUNT_ON_HOME_PAGE)

    def test_news_order(self):
        response = self.client.get(self.home_url)
        object_list = response.context['object_list']
        all_dates = [news.date for news in object_list]
        sorted_dates = sorted(all_dates, reverse=True)
        self.assertEqual(all_dates, sorted_dates)

    def test_comments_order(self):
        response = self.client.get(self.detail_url)
        self.assertIn('news', response.context)
        news = response.context['news']
        all_comments = news.comment_set.all()
        all_timestamps = [c.created for c in all_comments]
        self.assertEqual(all_timestamps, sorted(all_timestamps))

    def test_anonymous_client_has_no_form(self):
        response = self.client.get(self.detail_url)
        self.assertNotIn('form', response.context)

    def test_authorized_client_has_form(self):
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], CommentForm)
