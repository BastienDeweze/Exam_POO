from django.db import models
from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import ugettext as _

User = get_user_model()

class UserProfile(models.Model):
    
    """Classe repressantant le model du profil d'un utilisateur du site .

    user:
        Le user lié au profile.
    first_name:
        Le prénom de l'utilisateur
    last_name:
        Le nom de l'utilisateur
    number_of_purchase:
        Le nombre d'achat courant de l'utilisateur
    created_on:
        La date de création du profil
    updated_on:
        La dernière modification du profil
    reduction_threshold:
        Le nombre d'achat requis avant de bénéficier d'une réduction de 10%
    city:
        La ville de résidance
    """

    user = models.OneToOneField(User, related_name="user_profile", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, verbose_name='Nom', default='Nom')
    last_name = models.CharField(max_length=100, verbose_name='Prénom', default='Prénom')
    number_of_purchase = models.IntegerField(default=0, verbose_name="Nombre d'achat courant")
    total_number_of_purchase = models.IntegerField(default=0, verbose_name="Nombre d'achat total")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    reduction_threshold = models.IntegerField(default=10, verbose_name="Seuil de réduction")
    city = models.CharField(_("zip code"), max_length=4, default="0000")

    class Meta:
        ordering = ['-created_on']
        verbose_name = "Profile"

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):

        """
        Redefinition de la méthode "save" pour que le "self.slug" soit construit par rapport au username de l'utilisateur.
        """

        if not self.slug:
            self.slug = slugify(self.user.username)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):

        """
        Méthode qui supprime un utilisateur.
        Suppréssion du User qui va entrainer la suppression du profil.
        """

        User.objects.get(pk=self.user.id).delete()

    def get_absolute_url(self):
        return reverse('account:detail', args=[self.slug])

    def set_number_of_purchase(self, nb):

        """Méthode servant à modifier le nombre d'achat (total et courant) d'un profil.

        Args:
            nb (int): nombre d'achats à ajouter à l'existant

        Returns:
            bool: return True si le profil à droit à une réduction et False si le profile n'a pas droit à une reduction
        """

        self.total_number_of_purchase += nb
        if self.number_of_purchase + nb > self.reduction_threshold :
            self.number_of_purchase = 0
        else:
            self.number_of_purchase += nb
        self.save()
        return self.number_of_purchase == 0