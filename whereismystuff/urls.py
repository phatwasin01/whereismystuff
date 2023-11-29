from django.contrib import admin
from django.urls import path, include
from core.views import *
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', frontpage, name='frontpage'),
    path('book/create/manual', createBook, name='createbook'),
    path('book/create/ocr', createBookOCR, name='createbookOCR'),
    path('book/create/methods/', addBookMethods, name='addBookMethods'),
    path('book/edit/<int:id>', editBook, name='editbook'),
    path('book/<int:id>', viewBookById, name='viewbook'),
    path('profile/', viewProfileAndDashboard, name='profile'),
    path('profile/edit', editProfile, name='editprofile'),
    path('weekly_ranking/', getBestSellingBooks, name='weekly_ranking'),
    path('mylist/', viewBookTable, name='mylist'),
    path('accounts/login/', login_view, name='login'),
    path('accounts/logout/', logout_view, name='logout'),
    path('accounts/register/', register, name='register'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
