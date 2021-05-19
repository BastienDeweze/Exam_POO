from django.contrib import admin
from django.urls import path
from .views import ArticleHome, ArticleCreate, ArticleUpdate, ArticleDetail, ArticleDelete

app_name = "articles"

urlpatterns = [
    path('', ArticleHome.as_view(), name='home'),
    path('create/', ArticleCreate.as_view(), name='create'),
    path('<str:slug>', ArticleDetail.as_view(), name='detail'),
    path('edit/<str:slug>', ArticleUpdate.as_view(), name='edit'),
    path('delete/<str:slug>', ArticleDelete.as_view(), name='delete'),
]