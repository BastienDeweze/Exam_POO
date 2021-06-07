from django.contrib import admin
from django.urls import path
from .views import PanierCreate, PanierHome, CreateCommande, UniqueCommande, DeletePanier, CommandeHome, DeleteCommande, DetailCommande, MyOrders
from django.contrib.auth.decorators import login_required

app_name = "commande"

urlpatterns = [
    path('mon-panier', login_required(PanierHome.as_view(), login_url='account:login'), name='home'),
    path('create-panier/<str:slug>', login_required(PanierCreate.as_view(), login_url='account:login'), name='create-panier'),
    path('delete/<int:pk>', login_required(DeletePanier.as_view(), login_url='account:login'), name='delete'),
    path('delete-order/<int:pk>', login_required(DeleteCommande.as_view(), login_url='account:login'), name='delete-order'),
    path('detail-order/<int:pk>', login_required(DetailCommande.as_view(), login_url='account:login'), name='detail-order'),
    path('', login_required(CommandeHome.as_view(), login_url='account:login'), name='stat'),
    path('create-commande/', login_required(CreateCommande.as_view(), login_url='account:login'), name='create'),
    path('create-unique-commande/<str:slug>', login_required(UniqueCommande.as_view(), login_url='account:login'), name='create-unique'),
    path('my-orders/', login_required(MyOrders.as_view(), login_url='account:login'), name='my-orders'),
]