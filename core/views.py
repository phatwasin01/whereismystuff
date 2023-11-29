import json
from django.http import HttpResponse, JsonResponse, QueryDict
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import UserCreationForm

from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Book, BookType, Category
import requests
from django.core.cache import cache
from django.db.models import Count, Q
import base64
from asgiref.sync import sync_to_async
from django.core.files.storage import FileSystemStorage


@login_required
def frontpage(request):
    books = Book.objects.prefetch_related(
        'categories').filter(owner_id=request.user.id).filter(status='AVAILABLE' or 'BORROWED')
    categories = Category.objects.filter(books__owner=request.user).filter(
        books__status='AVAILABLE' or 'BORROWED').distinct()
    return render(request, 'core/mainpage.html', {
        'books': books,
        'categories': categories
    })


@login_required
def createBook(request):
    if request.method == 'POST':
        params = request.POST
        print(params)
        book_title = params['bookTitle']
        book_type = params['bookType']
        author = params['authorName']
        category_names = params.getlist('categories')
        language = params['language']
        status = params['status']
        publish_year = params['publishYear']
        try:
            picture = request.FILES['picture']
            fss = FileSystemStorage()
            file = fss.save(picture.name, picture)
            file_url = fss.url(file)
        except:
            file_url = ''
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
            cover_image_url=file_url,
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
    book_types = BookType.objects.exclude(name='Others').order_by('name')
    categories = Category.objects.exclude(name='Others').order_by('name')
    return render(request, 'books/createbook.html', {'book_types': book_types, 'categories': categories})


@login_required
def editBook(request, id):
    if request.method == 'PUT':
        putData = QueryDict(request.body)
        book = Book.objects.get(id=id)
        if book.owner != request.user:
            messages.error(
                request, "You don't have permission to edit this book")
            return HttpResponse(status=401, content='Unauthorized')
        book.title = putData.get('bookTitle', book.title)
        book.status = putData.get('status', book.status)
        book.author = putData.get('authorName', book.author)
        book.publish_year = int(putData.get('publishYear', book.publish_year))
        book.language = putData.get('language', book.language)
        category_names = putData.getlist('categories')
        book_type = putData.get('bookType', book.book_type)
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
            return redirect('viewbook', id=id)

        if type_obj is None:
            messages.error(request, "Book type doesn't exist")
            return redirect('viewbook', id=id)
        book.book_type = type_obj
        book.categories.set(categories_obj)
        book.save()
        return redirect('viewbook', id=id)
    book = Book.objects.get(id=id)
    book_types = BookType.objects.exclude(name='Others').order_by('name')
    categories = Category.objects.exclude(name='Others').order_by('name')
    checked_categories = [
        category.name for category in book.categories.all()]
    return render(request, 'books/editbook.html', {'book': book, 'book_types': book_types, 'categories': categories, 'checked_categories': checked_categories})


@login_required
def viewBookById(request, id: int):
    if request.method == 'DELETE':
        book = Book.objects.get(id=id)
        if book.owner != request.user:
            messages.error(
                request, "You don't have permission to delete this book")
            return HttpResponse(status=401, content='Unauthorized')
        try:
            book.delete()
            return HttpResponse(status=200)
        except:
            messages.error(request, "Failed to delete book")
            return HttpResponse(status=500)
    book = Book.objects.get(id=id)
    categories = book.categories.all()
    suggested_books = Book.objects.filter(
        book_type=book.book_type,
    ).filter(status='AVAILABLE' or 'BORROWED').filter(~Q(id=id))[:4]
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


async def getBestSellingBooks(request):
    # Check if user is authenticated
    is_authenticated = await sync_to_async(is_user_authenticated)(request.user)
    if not is_authenticated:
        return redirect('login')
    BASE_URL = 'https://api.nytimes.com/svc/books/v3/lists/current/'
    API_KEY = ''
    category_list = ['combined-print-and-e-book-nonfiction.json',
                     'combined-print-and-e-book-fiction.json']
    category_display = ['Non-Fiction', 'Fiction']

    books_data = []

    for category in category_list:
        cache_key = f'nyt_books_{category}'
        data = cache.get(cache_key)

        if not data:
            response = await sync_to_async(requests.get)(BASE_URL + category + '?api-key=' + API_KEY)
            data = response.json()
            cache.set(cache_key, data, timeout=3600)  # Cache for 1 hour
        books_data.append(data['results']['books'])

    return render(request, 'external/weekly_sales.html', {'nonfiction_books': books_data[0], 'fiction_books': books_data[1], 'category_display': category_display})


def is_user_authenticated(user):
    return user.is_authenticated


@login_required
def viewBookTable(request):
    if request.method == 'POST':
        search = request.POST['search']
        books = Book.objects.filter(owner=request.user).filter(
            Q(title__icontains=search) | Q(author__icontains=search) | Q(
                categories__name__icontains=search) | Q(
                book_type__name__icontains=search) | Q(
                language__icontains=search) | Q(
                    status__icontains=search)

        ).distinct()
        return render(request, 'books/bookTableRow.html', {'books': books})
    books = Book.objects.all().filter(owner=request.user)
    return render(request, 'books/book_table.html', {'books': books})


@login_required
def addBookMethods(request):
    word = "Action,Animal,BL,Chinese period,Contemporary literature,Depression,Drama,Fantasy,GL,Ghost,History,Horror,Inspiration,Isekai,Japanese period,Language,Literary,Magical,Mystery,Ocean,Parody,Period,Romance,Sci-fi,Slice of life,Social philosophy,Thriller,Others"
    word_list = word.split(",")
    print(word_list)
    return render(request, 'books/methodChoices.html')


@login_required
def createBookOCR(request):
    if request.method == 'POST':
        try:
            picture = request.FILES['picture']
        except:
            picture = None
        if picture is None:
            return HttpResponse(status=400, content="No image uploaded")
        base64_image = base64.b64encode(picture.read()).decode('utf-8')
        fss = FileSystemStorage()
        file = fss.save(picture.name, picture)
        file_url = fss.url(file)
        if not base64_image:
            return HttpResponse(status=400, content="parsin image failed")
        api_key = ""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Provide information of this book including title, author name, original language, publish year(only number), book type[choose only one(Fiction/Nonfiction/Cartoon/Literal/Novel/Biography/Knowledge/Others)] and catagories[choose multiple in this list:seperate with ',' witout spacing ('Action', 'Animal', 'BL', 'Chinese period', 'Contemporary literature', 'Depression', 'Drama', 'Fantasy', 'GL', 'Ghost', 'History', 'Horror', 'Inspiration', 'Isekai', 'Japanese period', 'Language', 'Literary', 'Magical', 'Mystery', 'Ocean', 'Parody', 'Period', 'Romance', 'Sci-fi', 'Slice of life', 'Social philosophy', 'Thriller', 'Others')]. (Don't tell me a sentence, give me only 6 short answers of following questions with '/' as a separator)"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        print(response.json())
        if response.status_code != 200:
            # delete file
            fss.delete(file)
            return HttpResponse(status=400, content="External api server error")
        text = response.json()['choices'][0]['message']['content']
        sep_text = text.split('/')
        book = {
            "title": sep_text[0],
            "author": sep_text[1],
            "language": sep_text[2],
            "publish_year": sep_text[3],
            "book_type": sep_text[4],
            "categories": sep_text[5].split(','),
        }
        try:
            categories_obj = Category.objects.filter(
                name__in=book['categories'])

        except:
            categories_obj = Category.objects.filter(name='Others')
        # check book type
        try:
            type_obj = BookType.objects.get(name=book['book_type'])
        except:
            type_obj = BookType.objects.get(name='Others')
        # save book to DB
        new_book = Book(
            title=book['title'],
            cover_image_url=file_url,
            status='AVAILABLE',
            author=book['author'],
            publish_year=book['publish_year'],
            language=book['language'],
            book_type=type_obj,
            owner=request.user,
        )
        new_book.save()
        if categories_obj:
            new_book.categories.set(categories_obj)
        return redirect('viewbook', id=new_book.id)  # type: ignore

    return render(request, 'books/uploadOCRImage.html')
