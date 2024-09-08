from django.contrib import admin
from myapp.models import Author, Genre, Book, BorrowRequest

admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(Book)
admin.site.register(BorrowRequest)
