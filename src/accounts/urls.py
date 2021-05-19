from django.contrib import admin
from django.urls import path, include
from .views import Login, Logout, SignUpView, ProfileUpdate, ProfileDetail, UserStat, ProfileDelete, ProfileUpdateAdmin
from django.contrib.auth.decorators import login_required

app_name = "account"

urlpatterns = [
    path('', login_required(UserStat.as_view(), login_url='account:login'), name='stat'),
    path('login/', Login.as_view(), name="login"),
    path('logout/', Logout.as_view(), name="logout"),
    path('<str:slug>', ProfileDetail.as_view(), name='detail'),
    path('signup/', SignUpView.as_view(), name="signup"),
    path('edit/<str:slug>', ProfileUpdate.as_view(), name='edit'),
    path('edit-admin/<str:slug>', ProfileUpdateAdmin.as_view(), name='edit-admin'),
    path('delete/<str:slug>', ProfileDelete.as_view(), name='delete'),
]