from django.db import models
from django.contrib.auth import get_user_model
from articles.models import Article
from django.urls import reverse
from django.template.defaultfilters import slugify
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.db.models import Sum

# Create your models here.

User = get_user_model()

class Panier(models.Model):

    """Classe represantant le panier d'un client (Commande non validée)

    user:
        Le user lié à la ligne de panier.
    articles:
        L'article lié à la ligne de panier.
    quantity:
        La quantité d'article souhaitée par l'utilisateur.
    price:
        La prix pour la ligne de panier.
    created_on:
        La date de la ligne de panier.
    updated_on:
        La dernière modification de la ligne de panier.
    """

    user = models.ForeignKey(User, related_name="panier_user", on_delete=models.CASCADE)
    articles = models.ForeignKey(Article, related_name="article_panier", on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0, validators=[ MinValueValidator(1) ], verbose_name="Quantité")
    price = models.FloatField(default=None, verbose_name='Prix')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('commande:home')

    def save(self, *args, **kwargs):

        """
        Redefinition de la méthode "save" pour que le "self.price" soit construit par rapport à l'article et à la quantité souhaitée.
        """
        
        self.price = self.articles.price * self.quantity

        super().save(*args, **kwargs)

class ValidatedOrder(models.Model):

    """Classe represant une commande validée par un utilisateur.

    user:
        Le user lié à la commande.
    articles:
        Les lignes d'article lié à la commande.
    tot_quantity:
        La quantité total d'article souhaitée par l'utilisateur (peu importe l'article).
    tot_price:
        La prix total de la commande.
    created_on:
        La date de création de la commande.
    reduction:
        True si la commande est l'objet d'une réduction, False si elle ne l'est pas.
    """

    user = models.ForeignKey(User, related_name="order_user", on_delete=models.CASCADE)
    articles = models.ManyToManyField(Article, through='LigneCommande', related_name="order_articles")
    tot_quantity = models.IntegerField(default=0, validators=[ MinValueValidator(1) ], verbose_name="Quantité", blank=True, null=True)
    tot_price = models.FloatField(default=None, verbose_name='Prix', blank=True, null=True)
    created_on = models.DateTimeField(default=timezone.now)
    reduction = models.BooleanField(default=False)

    def tot_price_and_quantity_calculation(self):

        """
        Méthode calculant "self.tot_quantity" et "self.tot_price" suivant les articles et le nombre d'articles se trouvant dans le panier de l'utilisateur.
        """

        panier = Panier.objects.filter(user=self.user)
        self.tot_price = panier.aggregate(Sum('price'))['price__sum']
        self.tot_quantity = panier.aggregate(Sum('quantity'))['quantity__sum']




class LigneCommande(models.Model):

    """Classe represantant une ligne de "ValidatedOrder"

    order:
        La commande à laquelle la ligne est liée.
    article:
        Un article de la commande.
    quantity:
        Le nombre d'article désiré.
    price:
        Le prix de la ligne.
    """
    order = models.ForeignKey(ValidatedOrder, related_name="order", on_delete=models.CASCADE)
    article = models.ForeignKey(Article, related_name="order_article", on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0, validators=[ MinValueValidator(1) ], verbose_name="Quantité")
    price = models.FloatField(default=None, verbose_name='Prix')

    def save(self, *args, **kwargs):
        """
        Redefinition de la méthode "save" pour que le "self.price" soit construit par rapport à l'article et à la quantité souhaitée.
        """
        self.price = self.article.price * self.quantity

        super().save(*args, **kwargs)