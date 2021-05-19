from django.shortcuts import render
from django.views.generic import ListView, CreateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView
from .models import Article
from django.db.models import Q
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Create your views here.

class ArticleHome(ListView):
    model = Article
    context_object_name = "articles"

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        print(query)
        print(queryset)

        if query is not None :
            if self.request.user.is_authenticated and self.request.user.is_superuser:
                return queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))


            else:
                return queryset.filter(Q(name__icontains=query) | Q(description__icontains=query)).filter(published=True)

        elif self.request.user.is_authenticated and self.request.user.is_superuser:
            if 'q1' in self.request.GET:
                return queryset.order_by('-total_number_of_purchase')[:3]
            if 'q2' in self.request.GET:
                return queryset.order_by('total_number_of_purchase')[:3]
            if 'q3' in self.request.GET:
                return queryset.filter(stock__lte=5)
            return queryset

        return queryset.filter(published=True)

@method_decorator(login_required, name='dispatch')
class ArticleCreate(CreateView):
    model = Article
    template_name = "articles/create_article.html"
    fields = ['name', 'description', 'price']

class ArticleUpdate(UpdateView):
    model = Article
    template_name = "articles/create_edit.html"
    fields = ['name', 'description', 'price', 'published']

class ArticleDetail(DetailView):
    model = Article
    context_object_name = "article"

class ArticleDelete(DeleteView):
    model = Article
    success_url = reverse_lazy('articles:home')
    context_object_name = "article"