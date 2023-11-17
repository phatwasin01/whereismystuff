import datetime
import json
from django.http import HttpResponse, JsonResponse, QueryDict
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import UserCreationForm

from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Book, BookType, Category
import requests
from threading import Thread
from django.core.cache import cache
from django.db.models import Count, Q


@login_required
def frontpage(request):
    books = Book.objects.prefetch_related(
        'categories').filter(owner_id=request.user.id)
    categories = Category.objects.filter(books__owner=request.user).distinct()
    return render(request, 'core/mainpage.html', {
        'books': books,
        'categories': categories
    })


@login_required
def createBook(request):
    book_types = BookType.objects.exclude(name='Others').order_by('name')
    categories = Category.objects.exclude(name='Others').order_by('name')
    return render(request, 'books/createbook.html', {'book_types': book_types, 'categories': categories})


@login_required
def editBook(request, id):
    book = Book.objects.get(id=id)
    return render(request, 'books/editbook.html', {'id': book.id     # type: ignore
                                                   })


@login_required
def viewBookById(request, id: int):
    if request.method == 'DELETE':
        book = Book.objects.get(id=id)
        try:
            book.delete()
            return HttpResponse(status=200)
        except:
            return HttpResponse(status=500)
    book = Book.objects.get(id=id)
    categories = book.categories.all()
    print(categories)
    suggested_books = Book.objects.filter(
        book_type=book.book_type,
    )[:4]
    return render(request, 'books/viewbook.html', {'book': book, 'suggested_books': suggested_books, 'categories': categories})


@login_required
def viewProfileAndDashboard(request):
    if request.method == 'PUT':
        putData = QueryDict(request.body)
        user = request.user
        user.username = putData.get('username', user.username)
        user.email = putData.get('email', user.email)
        user.first_name = putData.get('first_name', user.first_name)
        user.last_name = putData.get('last_name', user.last_name)
        user.save()
        context = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        return render(request, 'auth/profileInput.html', {'context': context})
    username = request.user.username
    email = request.user.email
    first_name = request.user.first_name
    last_name = request.user.last_name

    # Annotating categories with the count of books owned by the user
    categories = Category.objects.annotate(
        book_count=Count('books', filter=Q(books__owner=request.user))
    ).distinct()

    category_data = [{'name': category.name,
                      'value': category.book_count} for category in categories]  # type: ignore
    # filter categories with 0 books
    category_data_filter = [
        category for category in category_data if category['value'] > 0]

    context = {
        'username': username,
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
    }
    dashboard_data = {
        'category_data': json.dumps(category_data_filter)
    }

    return render(request, 'auth/profile.html', {'context': context, 'dashboard_data': dashboard_data})


def editProfile(request):
    return render(request, 'auth/editprofile.html')


@login_required
def addBooks(request):
    if request.method == 'POST':
        params = request.POST
        book_title = params['bookTitle']
        book_type = params['bookType']
        author = params['authorName']
        category_names = params.getlist('categories')
        language = params['language']
        status = params['status']
        publish_year = params['publishYear']
        # check category
        try:
            categories_obj = Category.objects.filter(name__in=category_names)
        except:
            categories_obj = None
        # check book type
        try:
            type_obj = BookType.objects.get(name=book_type)
        except:
            type_obj = None

        if not (categories_obj != None and categories_obj.exists()):
            messages.error(request, "Category doesn't exist")
            return HttpResponse(status=500, content='')

        if type_obj is None:
            messages.error(request, "Book type doesn't exist")
            return HttpResponse(status=500, content='')
        new_book = Book(
            title=book_title,
            cover_image_url='',
            status=status,
            author=author,
            publish_year=publish_year,
            language=language,
            book_type=type_obj,
            owner=request.user,
        )
        new_book.save()
        new_book.categories.set(categories_obj)
        return render(request, 'books/addedbook.html', {'new_book': new_book, 'categories': categories_obj, 'book_type': type_obj})
    else:
        return HttpResponse(status=500, content='')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('frontpage')
        else:
            print(form.errors)
    else:
        form = UserCreationForm()
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('frontpage')  # Redirect to a success page.
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'auth/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def getBestSellingBooks(request):
    BASE_URL = 'https://api.nytimes.com/svc/books/v3/lists/current/'
    API_KEY = 'GwjdK16uSaRrs2OSjdgOg9LBJyZqsmBe'
    category_list = ['combined-print-and-e-book-nonfiction.json',
                     'combined-print-and-e-book-fiction.json']
    category_display = ['Non-Fiction', 'Fiction']

    books_data = []

    for category in category_list:
        cache_key = f'nyt_books_{category}'
        data = cache.get(cache_key)

        if not data:
            response = requests.get(
                BASE_URL + category + '?api-key=' + API_KEY)
            data = response.json()
            cache.set(cache_key, data, timeout=3600)  # Cache for 1 hour
        books_data.append(data['results']['books'])

    return render(request, 'external/weekly_sales.html', {'nonfiction_books': books_data[0], 'fiction_books': books_data[1], 'category_display': category_display})
