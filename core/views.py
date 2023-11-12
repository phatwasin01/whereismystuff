from django.http import HttpResponse
from django.shortcuts import render, redirect
import random
from django.contrib.auth import login, authenticate, logout
from .forms import UserCreationForm

from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Book, BookType, Category, Friend


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
    if (request.method == 'POST'):
        print(request.POST)
        return
    book_types = BookType.objects.exclude(name='Others').order_by('name')
    categories = Category.objects.exclude(name='Others').order_by('name')
    return render(request, 'books/createbook.html', {'book_types': book_types, 'categories': categories})


@login_required
def editBook(request, id):
    book = Book.objects.get(id=id)
    return render(request, 'books/editbook.html', {'id': book.id, })


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
def viewProfile(request):
    if request.method == 'PUT':
        putData = request.PUT
        print(putData)
        user = request.user
        user.username = putData['username']
        user.email = putData['email']
        user.first_name = putData['first_name']
        user.last_name = putData['last_name']
        user.save()
    username = request.user.username
    email = request.user.email
    first_name = request.user.first_name
    last_name = request.user.last_name
    context = {
        'username': username,
        'email': email,
        'first_name': first_name,
        'last_name': last_name
    }

    return render(request, 'auth/profile.html', context)


def editProfile(request):
    return render(request, 'auth/editprofile.html')


@login_required
def addBooks(request):
    print(request.POST)
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

        if not categories_obj.exists():
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
        print(categories_obj)
        new_book.categories.set(categories_obj)
        return render(request, 'books/addedbook.html', {'new_book': new_book, 'categories': categories_obj, 'book_type': type_obj})


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
