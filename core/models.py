from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

BOOK_STATUS_CHOICES = [
    ('AVAILABLE', 'Available'),
    ('BORROWED', 'Borrowed'),
    ('DELETED', 'Deleted'),
]


class Friend(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='friends')
    friend = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='friend_of')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'friend'),)
        constraints = [
            models.CheckConstraint(check=~models.Q(user=models.F(
                'friend')), name='user_not_friend_with_self'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.friend.username}"


class BookType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    cover_image_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=20, choices=BOOK_STATUS_CHOICES, default='AVAILABLE')
    author = models.CharField(max_length=255)
    publish_year = models.PositiveIntegerField()
    language = models.CharField(max_length=255)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='owned_books')
    book_type = models.ForeignKey(
        BookType, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    categories = models.ManyToManyField(Category, related_name='books')
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
