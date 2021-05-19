from django.db import models
from django.contrib.auth import get_user_model
from articles.models import Article
from django.urls import reverse
from django.template.defaultfilters import slugify
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.

User = get_user_model()

class Panier(models.Model):
    user = models.ForeignKey(User, related_name="panier_user", on_delete=models.CASCADE)
    articles = models.ForeignKey(Article, related_name="article_panier", on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0, validators=[ MinValueValidator(1) ], verbose_name="Quantité")
    price = models.FloatField(default=None, verbose_name='Prix')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('commande:home')

    def save(self, *args, **kwargs):
        
        self.price = self.articles.price * self.quantity

        super().save(*args, **kwargs)

class ValidatedOrder(models.Model):
    user = models.ForeignKey(User, related_name="order_user", on_delete=models.CASCADE)
    articles = models.ManyToManyField(Article, through='LigneCommande', related_name="order_articles")
    tot_quantity = models.IntegerField(default=0, validators=[ MinValueValidator(1) ], verbose_name="Quantité")
    tot_price = models.FloatField(default=None, verbose_name='Prix')
    created_on = models.DateTimeField(auto_now_add=True)
    reduction = models.BooleanField(default=False)


class LigneCommande(models.Model):
    order = models.ForeignKey(ValidatedOrder, related_name="order", on_delete=models.CASCADE)
    article = models.ForeignKey(Article, related_name="order_article", on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0, validators=[ MinValueValidator(1) ], verbose_name="Quantité")
    price = models.FloatField(default=None, verbose_name='Prix')

    def save(self, *args, **kwargs):
        self.price = self.article.price * self.quantity

        super().save(*args, **kwargs)