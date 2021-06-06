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
from django.db.models import Sum

from django.contrib import messages

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

    def test_func(self, *args, **kwargs):
        return self.request.user.is_superuser or slugify(self.request.user.username) == self.kwargs['slug']

class ProfileUpdateAdmin(ProfileUpdate):
    template_name = "account/create_edit_admin.html"
    fields = ['first_name', 'last_name', 'city', 'reduction_threshold']
    success_url = reverse_lazy('account:stat')


class ProfileDelete(UserPassesTestMixin, DeleteView):
    model = UserProfile
    template_name = "account/userprofile_confirm_delete.html"
    success_url = reverse_lazy('articles:home')
    context_object_name = "userprofile"

    def test_func(self, *args, **kwargs):
        return self.request.user.is_superuser or slugify(self.request.user.username) == self.kwargs['slug']

class Logout(LogoutView):
    pass

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
        query = self.request.GET.get('q')

        if query is not None :
            if 'q' in self.request.GET:
                return queryset.filter(Q(last_name__icontains=query) | Q(first_name__icontains=query))

        elif 'q1' in self.request.GET:
            req = self.request.GET['q1']

            if req == "Top client":
                return queryset.filter(total_number_of_purchase=queryset.aggregate(Max('total_number_of_purchase'))['total_number_of_purchase__max'])

            elif req == "Nul client":
                return queryset.filter(total_number_of_purchase=queryset.aggregate(Min('total_number_of_purchase'))['total_number_of_purchase__min'])

            elif req == "Top ville client":
                return self.get_top_city(queryset)

        return queryset

    def get_top_city(self, queryset):
        lst_city = UserProfile.objects.order_by().values('city').distinct()
        userprofile = UserProfile.objects.all()
        dct_count = {}

        for i in lst_city:
            count = userprofile.filter(city=i['city']).aggregate(Sum('total_number_of_purchase'))['total_number_of_purchase__sum']
            dct_count[i['city']] = count

        max_value = max(dct_count.values())
        top_city = [k for k, v in dct_count.items() if v == max_value]
        messages.info(self.request, f"Zipcode des meilleures villes :  {' '.join(top_city)}")
        return queryset.filter(city__in=top_city)