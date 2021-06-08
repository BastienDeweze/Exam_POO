from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from .models import UserProfile
from django.views.generic.detail import DetailView
from eSchop.views import UserPassesTestMixinCustom
from django.contrib.auth import get_user_model
from django.views.generic import ListView
from django.db.models import Q, Max, Min
from django.template.defaultfilters import slugify
from django.db.models import Sum
from .forms import UserRegisterForm
from django.views.generic.edit import CreateView

from django.contrib import messages

User = get_user_model()


class Login(LoginView):

    """
    LoginView servant à loger un utilisateur
    """

    template_name="account/login.html"
    redirect_authenticated_user = True

class ProfileDetail(DetailView):

    """
    DetailView affichant les detail d'une profil en particulié.
    """

    model = UserProfile
    context_object_name = "userprofile"
    template_name = "account/profile.html"

class ProfileUpdate(UserPassesTestMixinCustom, UpdateView):

    """
    UpdateView modifiant le contenu d'un profile. Réservé à tout les utilisateurs.
    """

    model = UserProfile
    template_name = "account/create_edit.html"
    fields = ['first_name', 'last_name', 'city']

    def test_func(self, *args, **kwargs):

        """Redefinition de "UserPassesTestMixinCustom.test_func()" verifiant que l'utilisateur faisant la requete est bien un superuser ou l'utilisateur ayant créé la ligne.

        Returns:
            bool: True si l'utilisateur est autorisé et Fase si il ne l'est pas.
        """

        return super().test_func(self, *args, **kwargs) or slugify(self.request.user.username) == self.kwargs['slug']

class ProfileUpdateAdmin(ProfileUpdate):

    """
    UpdateView modifiant le contenu d'un profile. Réservé exclusivement aux superuser.
    """


    template_name = "account/create_edit_admin.html"
    fields = ['first_name', 'last_name', 'city', 'reduction_threshold']
    success_url = reverse_lazy('account:stat')

    def test_func(self, *args, **kwargs):

        """Redefinition de "UserPassesTestMixinCustom.test_func()" verifiant que l'utilisateur faisant la requete est bien un superuser ou l'utilisateur ayant créé la ligne.

        Returns:
            bool: True si l'utilisateur est autorisé et Fase si il ne l'est pas.
        """

        return self.request.user.is_superuser

class ProfileDelete(UserPassesTestMixinCustom, DeleteView):

    """
    DeleteView supprimant des comptes completement.
    """

    model = UserProfile
    template_name = "account/userprofile_confirm_delete.html"
    success_url = reverse_lazy('articles:home')
    context_object_name = "userprofile"

    def test_func(self, *args, **kwargs):

        """Redefinition de "UserPassesTestMixinCustom.test_func()" verifiant que l'utilisateur faisant la requete est bien un superuser ou l'utilisateur ayant créé la ligne.

        Returns:
            bool: True si l'utilisateur est autorisé et False si il ne l'est pas.
        """

        return super().test_func(self, *args, **kwargs) or slugify(self.request.user.username) == self.kwargs['slug']

class Logout(LogoutView):

    """
    LogoutView servant à logout un utilisateur
    """

    pass


class SignUpView(SuccessMessageMixin, CreateView):

    """
    CreateView creant un compte et un profil d'utilisateur.
    """

    template_name = 'account/signup.html'
    success_url = reverse_lazy('account:login')
    form_class = UserRegisterForm
    success_message = "Your profile was created successfully"


class UserStat(UserPassesTestMixinCustom, ListView):

    """
    ListView affichant toutes les compte utilisateur du site sans exeption, reservé aux superusers.
    """

    model = UserProfile
    context_object_name = "userprofile"
    template_name = "account/userprofile_list.html"

    def get_queryset(self):

        """Fonction modifiant le queryset de compte selon la requete du superuser.
            Reservé aux supperusers.

            Tri possible : top 1 meilleur client, top 1 moins bon client, top 1 (ou plus si égalité) de la ville qui achete le plus.

        Returns:
            QuerySet: Les users trié.
        """

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

        """Fonction renvoyant le queryset des utilisateurs habitant dans la (ou les) ville qui achete le plus.

        Args:
            queryset (QuerySet): Queryset de tout les utilisateurs inscrit sur le site.

        Returns:
            QuerySet: Queryset trié, lessant seulement les utilisateurs de la (ou les) top ville
        """
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