from django.shortcuts import render
from django.views.generic import ListView, CreateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView
from .models import Article, Category
from django.db.models import Q
from django.urls import reverse_lazy
from eSchop.views import UserPassesTestMixinCustom
from django.contrib import messages

class ArticleHome(ListView):

    """
    ListView listant les articles du shop.
    """

    model = Article
    context_object_name = "articles"

    def get_queryset(self):

        """Fonction modifiant le queryset de commandes selon la requete de l'utilisateur.

            Tri possible : top 3 de meilleures ventes, top 3 des pires ventes, alerte de stock. (réservé superuser)

        Returns:
            QuerySet: Les articles trié.
        """

        queryset = super().get_queryset()
        queryset = queryset if self.request.user.is_superuser else queryset.filter(published=True)
        query = self.request.GET.get('q')
        query_1 = self.request.GET.get('q1')

        if query :
            if query in Category.objects.values_list('name', flat=True):
                return queryset.filter(Q(categories__name=query))
            return queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))

        elif query_1 and self.request.user.is_authenticated and self.request.user.is_superuser:
            
            if query_1 == 'Top ventes':
                return queryset.order_by('-total_number_of_purchase')[:3]

            elif query_1 == 'Nul ventes':
                return queryset.order_by('total_number_of_purchase')[:3]

            elif query_1 == 'Alerte stock':
                return queryset.filter(stock__lte=5)

        return queryset


class ArticleCreate(UserPassesTestMixinCustom, CreateView):

    """
    CreateView créant un article. (réservé superuser)
    """

    model = Article
    template_name = "articles/create_article.html"
    fields = ['name', 'description', 'price', 'categories', 'thumbnail']
    


class ArticleUpdate(UserPassesTestMixinCustom, UpdateView):

    """
    UpdateView modifiant le contenu d'une ligne d'article.
    """

    model = Article
    template_name = "articles/create_edit.html"
    fields = ['thumbnail', 'name', 'description', 'price', 'stock', 'published']

class ArticleDetail(DetailView):

    """
    DetailView affichant les detail d'un article en particulié.
    """

    model = Article
    context_object_name = "article"

class ArticleDelete(UserPassesTestMixinCustom, DeleteView):

    """
    DeleteView supprimant des articles, reservé aux superusers.
    """

    model = Article
    success_url = reverse_lazy('articles:home')
    context_object_name = "article"