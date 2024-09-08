from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Author(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField()
    isbn = models.CharField(max_length=13, unique=True)
    available = models.BooleanField(default=True)
    published_date = models.DateField()
    publisher = models.CharField(max_length=255)
    genres = models.ManyToManyField(Genre, related_name='books', blank=True)
    authors = models.ManyToManyField(Author, related_name='books')
    borrower = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title


class BorrowRequest(models.Model):
    PENDING = 1
    APPROVED = 2
    COLLECTED = 3
    COMPLETE = 4
    DECLINED = 5

    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (COLLECTED, 'Collected'),
        (COMPLETE, 'Complete'),
        (DECLINED, 'Declined'),
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_requests')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrow_requests')
    status = models.IntegerField(choices=STATUS_CHOICES, default=PENDING)
    overdue = models.BooleanField(default=False)
    request_date = models.DateTimeField(default=timezone.now)
    approval_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    complete_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.borrower} - {self.book.title} (Status: {self.get_status_display()})"
