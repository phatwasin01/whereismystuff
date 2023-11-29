from django.contrib import admin
from .models import Book, BookType, Category

# Register your models here.
admin.site.register(Book)
admin.site.register(BookType)
admin.site.register(Category)
