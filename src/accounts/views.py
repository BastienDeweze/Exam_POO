from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from .models import UserProfile
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.views.generic import ListView
from django.db.models import Q, Max, Min
from django.template.defaultfilters import slugify

User = get_user_model()

# Create your views here.

class Login(LoginView):
    template_name="account/login.html"
    redirect_authenticated_user = True

class ProfileDetail(DetailView):
    model = UserProfile
    context_object_name = "userprofile"
    template_name = "account/profile.html"

class ProfileUpdate(UserPassesTestMixin, UpdateView):
    model = UserProfile
    template_name = "account/create_edit.html"
    fields = ['first_name', 'last_name', 'city']
    #success_url = reverse_lazy('account:detail')

    def get_context_data(self, **kwargs):
        print(self.kwargs)
        print(super().get_context_data(**kwargs))
        return super().get_context_data(**kwargs)

    def test_func(self, *args, **kwargs):
        return self.request.user.is_superuser or slugify(self.request.user.username) == self.kwargs['slug']

class ProfileUpdateAdmin(ProfileUpdate):
    template_name = "account/create_edit_admin.html"
    fields = ['first_name', 'last_name', 'city', 'reduction_threshold']


class ProfileDelete(UserPassesTestMixin, DeleteView):
    model = UserProfile
    template_name = "account/userprofile_confirm_delete.html"
    success_url = reverse_lazy('articles:home')
    context_object_name = "userprofile"

    def test_func(self, *args, **kwargs):
        return self.request.user.is_superuser or slugify(self.request.user.username) == self.kwargs['slug']

class Logout(LogoutView):
    pass
    #template_name="account/logout.html"
    #redirect_authenticated_user = True

from .forms import UserRegisterForm
from django.views.generic.edit import CreateView

class SignUpView(SuccessMessageMixin, CreateView):
  template_name = 'account/signup.html'
  success_url = reverse_lazy('account:login')
  form_class = UserRegisterForm
  success_message = "Your profile was created successfully"


class UserStat(UserPassesTestMixin, ListView):
    model = UserProfile
    context_object_name = "userprofile"
    template_name = "account/userprofile_list.html"

    def test_func(self, *args, **kwargs):
        return self.request.user.is_superuser

    def get_queryset(self):
        queryset = super().get_queryset()
        print(queryset)
        query = self.request.GET.get('q')
        print(query)
        print(queryset[0].user.id)
        print(self.kwargs)

        if query is not None :
            if 'q' in self.request.GET:
                print("coucou")
                return queryset.filter(Q(last_name__icontains=query) | Q(first_name__icontains=query))
        if 'q1' in self.request.GET:
            print("coucou")
            return queryset.filter(total_number_of_purchase=queryset.aggregate(Max('total_number_of_purchase'))['total_number_of_purchase__max'])
        if 'q2' in self.request.GET:
            print("coucou")
            return queryset.filter(total_number_of_purchase=queryset.aggregate(Min('total_number_of_purchase'))['total_number_of_purchase__min'])
        if 'q3' in self.request.GET:
            print("coucou")
            return queryset.filter(Q(last_name__icontains=query) | Q(first_name__icontains=query))
        return queryset