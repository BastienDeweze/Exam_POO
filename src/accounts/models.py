from django.db import models
from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import ugettext as _

User = get_user_model()

class UserProfile(models.Model):
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

        if not self.slug:
            self.slug = slugify(self.user.username)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        User.objects.get(pk=self.user.id).delete()

    def get_absolute_url(self):
        return reverse('account:detail', args=[self.slug])