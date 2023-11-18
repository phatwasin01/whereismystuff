from django.contrib import admin
from django.urls import path, include
from core.views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', frontpage, name='frontpage'),
    path('book/create', createBook, name='createbook'),
    path('book/edit/<int:id>', editBook, name='editbook'),
    path('book/<int:id>', viewBookById, name='viewbook'),
    path('profile/', viewProfileAndDashboard, name='profile'),
    path('profile/edit', editProfile, name='editprofile'),
    path('book/add', addBooks, name='addBooks'),
    path('weekly_ranking/', getBestSellingBooks, name='weekly_ranking'),
    path('mylist/', viewBookTable, name='mylist'),
    path('accounts/login/', login_view, name='login'),
    path('accounts/logout/', logout_view, name='logout'),
    path('accounts/register/', register, name='register'),

]
