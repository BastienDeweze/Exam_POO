from django.contrib import admin
from django.urls import path
from .views import PanierCreate, PanierHome, CreateCommande, UniqueCommande, DeletePanier, CommandeHome
from django.contrib.auth.decorators import login_required

app_name = "commande"

urlpatterns = [
    path('mon-panier', login_required(PanierHome.as_view(), login_url='account:login'), name='home'),
    path('create-panier/<str:slug>', login_required(PanierCreate.as_view(), login_url='account:login'), name='create-panier'),
    path('delete/<int:pk>', login_required(DeletePanier.as_view(), login_url='account:login'), name='delete'),
    path('', CommandeHome.as_view(), name='edit'),
    path('create-commande/', CreateCommande.as_view(), name='create'),
    path('create-unique-commande/<str:slug>', UniqueCommande.as_view(), name='create-unique'),
]