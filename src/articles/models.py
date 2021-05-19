from django.db import models
from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
from django.urls import reverse

User = get_user_model()

class Article(models.Model):
    name = models.CharField( max_length=255, unique=True, verbose_name='Nom')
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    publisher = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default='', blank=True, null=True)
    price = models.FloatField(default=None, verbose_name='Prix')
    total_number_of_purchase = models.IntegerField(default=0, verbose_name="Nombre d'achat total")
    stock = models.IntegerField(default=0, verbose_name="Stock")
    last_updated = models.DateTimeField(auto_now=True)
    created_on = models.DateField(blank=True, null=True)
    published = models.BooleanField(default=False, verbose_name='Publié')
    description = models.TextField(blank=True, verbose_name='Description')

    class Meta:
        ordering = ['-created_on']
        verbose_name = "Article"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("articles:home")
    