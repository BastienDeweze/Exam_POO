from django.db import models
from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone

User = get_user_model()

class Category(models.Model):

    """Classe représantant une catégorie d'articles du shop

    name:
        Le nom de la catégorie.
    description:
        Le description de la catégorie
    created_on:
        La date de création du profil.
    """

    name = models.CharField( max_length=255, unique=True, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    created_on = models.DateField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.name
    

class Article(models.Model):

    """Classe représantant un article du shop

    name:
        Le nom d'un article.
    publisher:
        L'utilisateur ayant enregistré l'article.
    price:
        Le prix de l'article
    total_number_of_purchase:
        Le nombre total de vente de l'article.
    stock:
        Le stock de l'article.
    last_updated:
        La dernière modification de l'article.
    published:
        L'état de publication de l'article
    published:
        L'état de publication de l'article
    description:
        Le description d'un article.
    categories:
        Les catégories dans lesquelles se trouvent l'articles.
    thumbnail:
        L'image de l'article.
    created_on:
        La date de création de l'article.
    """

    name = models.CharField( max_length=255, unique=True, verbose_name='Nom')
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    publisher = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default='', blank=True, null=True)
    price = models.FloatField(default=None, verbose_name='Prix')
    total_number_of_purchase = models.IntegerField(default=0, verbose_name="Nombre d'achat total")
    stock = models.IntegerField(default=0, verbose_name="Stock")
    last_updated = models.DateTimeField(auto_now=True)
    created_on = models.DateField(blank=True, null=True, auto_now=True)
    published = models.BooleanField(default=False, verbose_name='Publié')
    description = models.TextField(blank=True, verbose_name='Description')
    categories = models.ManyToManyField(Category)
    thumbnail = models.ImageField(blank=True, upload_to='articles', default='mediafiles\\articles\\logo.png', verbose_name="Image de l'article")

    class Meta:
        ordering = ['-created_on']
        verbose_name = "Article"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        """
        Redefinition de la méthode "save" pour que le "self.slug" soit construit par rapport au nom complet de l'article.
        """

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("articles:home")

    def set_stock(self, quantity):

        """Fonction servant à modifier le stock de l'article suite à une commande.

        Args:
            quantity (int): nombre d'achats fait par le client.

        Returns:
            int or None: Le nombre d'article manquant si le stock est insufisant, sinon None.
        """

        self.total_number_of_purchase += quantity
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
        else :
            miss = self.stock - quantity
            self.stock = 0
            self.save()
            return abs(miss)
    