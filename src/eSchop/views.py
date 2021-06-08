from django.shortcuts import render
from django.contrib.auth.mixins import UserPassesTestMixin


class UserPassesTestMixinCustom(UserPassesTestMixin):

    """
    Modification de UserPassesTestMixin
    """

    def test_func(self, *args, **kwargs):

        """Fonction verifiant que l'utilisateur faisant la requete est bien un superuser.

        Returns:
            bool: True si l'utilisateur est autorisé et Fase si il ne l'est pas.
        """

        return self.request.user.is_superuser

def index(request):
    return render(request, 'index.html')