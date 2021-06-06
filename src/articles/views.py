from django.shortcuts import render
from django.views.generic import ListView, CreateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView
from .models import Article, Category
from django.db.models import Q
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin

from django.contrib import messages

# Create your views here.

class ArticleHome(ListView):
    model = Article
    context_object_name = "articles"

    def get_queryset(self):
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

@method_decorator(login_required, name='dispatch')
class ArticleCreate(UserPassesTestMixin, CreateView):
    model = Article
    template_name = "articles/create_article.html"
    fields = ['name', 'description', 'price', 'categories', 'thumbnail']

    def test_func(self, *args, **kwargs):
        return self.request.user.is_superuser

    def form_valid(self, form) :
        return super().form_valid(form)
    


class ArticleUpdate(UserPassesTestMixin, UpdateView):
    model = Article
    template_name = "articles/create_edit.html"
    fields = ['thumbnail', 'name', 'description', 'price', 'stock', 'published']

    def test_func(self, *args, **kwargs):
        return self.request.user.is_superuser

    def form_valid(self, form) :
        return super().form_valid(form)

class ArticleDetail(DetailView):
    model = Article
    context_object_name = "article"

class ArticleDelete(UserPassesTestMixin, DeleteView):
    model = Article
    success_url = reverse_lazy('articles:home')
    context_object_name = "article"

    def test_func(self, *args, **kwargs):
        return self.request.user.is_superuser