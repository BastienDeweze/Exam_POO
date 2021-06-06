from django.test import TestCase
from articles.models import Article
from .models import Panier, ValidatedOrder, LigneCommande
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models import Sum
from datetime import datetime, timedelta

# Create your tests here.

class TestPanier(TestCase):

    def setUp(self):
        self.article = Article.objects.create(name='Article test', 
                                                published=0,
                                                price=2.5,
                                                description="Une super description d'article",
                                                        )

        self.user = get_user_model().objects.create(first_name='name_test', 
                                                        username='test',
                                                        password='12test12',
                                                        email='test@example.com',
                                                        is_superuser=0)

    def test_create_panier(self):
        self.client.force_login(self.user)
        data = {
            "quantity": 20
        }

        response = self.client.post(reverse('commande:create-panier', kwargs={'slug': self.article.slug}), data)
        self.assertEqual(response.status_code, 302)
        panier = Panier.objects.filter(user = self.user)
        
        self.assertTrue(len(panier) == 1)
        self.assertEqual(panier.aggregate(Sum('quantity'))['quantity__sum'], 20)


    def test_datail_panier(self):
        self.client.force_login(self.user)
        response_get_panier = self.client.get('/order/mon-panier')

        self.assertEqual(response_get_panier.status_code, 200)
        self.assertEqual(len(response_get_panier.context['panier']), 0)
        self.assertEqual(response_get_panier.context['price_tot'], None)
        self.assertEqual(response_get_panier.context['nb_art_tot'], None)

        data = {
            "quantity": 20
        }

        self.client.post(reverse('commande:create-panier', kwargs={'slug': self.article.slug}), data)
        response_get_panier = self.client.get('/order/mon-panier')
        self.assertEqual(len(response_get_panier.context['panier']), 1)
        self.assertEqual(response_get_panier.context['price_tot'], data["quantity"] * self.article.price )
        self.assertEqual(response_get_panier.context['nb_art_tot'], data["quantity"])

    def test_delete_panier(self):
        self.client.force_login(self.user)
        slug = self.article.slug

        data = {
            "quantity": 20
        }
        self.client.post(reverse('commande:create-panier', kwargs={'slug': self.article.slug}), data)

        panier = Panier.objects.filter(user = self.user)
        lenQueryset = len(panier)
        self.assertEqual(lenQueryset, 1)

        response = self.client.post(reverse('commande:delete', kwargs={'pk': panier[0].id}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(Panier.objects.filter(user = self.user)), 0)

class TestCommande(TestCase):

    def setUp(self):
        self.article = Article.objects.create(name='Article test', 
                                                published=0,
                                                price=2.5,
                                                stock=10,
                                                description="Une super description d'article",
                                                        )

        self.deuxieme_article = Article.objects.create(name='Deuxième article test', 
                                                published=0,
                                                price=6.99,
                                                stock=10,
                                                description="Une super description d'un deuxieme article",
                                                        )

        self.user = get_user_model().objects.create(first_name='name_test', 
                                                        username='test_1',
                                                        password='12test12',
                                                        email='test@example.com',
                                                        is_superuser=0)

        self.user_2 = get_user_model().objects.create(first_name='name_test_2', 
                                                        username='test_2',
                                                        password='12test123',
                                                        email='test_2@example.com',
                                                        is_superuser=1)
        
        Panier.objects.create(quantity=5, articles=self.article, user=self.user)
        Panier.objects.create(quantity=7, articles=self.deuxieme_article, user=self.user)

        Panier.objects.create(quantity=5, articles=self.article, user=self.user_2)
        Panier.objects.create(quantity=4, articles=self.deuxieme_article, user=self.user_2)

        self.panier = Panier.objects.filter(user = self.user)
        self.panier_2 = Panier.objects.filter(user = self.user)

    
    def test_create_commande(self):

        self.client.force_login(self.user)
        response = self.client.post(reverse('commande:create'))
        self.assertEqual(response.status_code, 302)

        order = ValidatedOrder.objects.get(pk=1)
        
        self.assertTrue(order)
        self.assertEqual(order.tot_quantity, 12)
        self.assertEqual(order.tot_price, 61.43)
        self.assertEqual(order.user, self.user)
        self.assertTrue(order.reduction)

        ligne_order = LigneCommande.objects.filter(order=order)

        self.assertEqual(len(ligne_order), 2)
        self.assertEqual(ligne_order[0].article, self.article)
        self.assertEqual(ligne_order[0].price, self.article.price * 5)

        self.assertEqual(ligne_order[1].article, self.deuxieme_article)
        self.assertEqual(ligne_order[1].price, self.deuxieme_article.price * 7)


    def test_reduction_and_dell_panier(self):

        self.client.force_login(self.user)

        response = self.client.post(reverse('commande:create'))

        order = ValidatedOrder.objects.get(pk=1)

        self.assertTrue(order.reduction)
        self.assertEqual(len(Panier.objects.filter(user = self.user)), 0)


        self.client.force_login(self.user_2)

        response = self.client.post(reverse('commande:create'))
        order = ValidatedOrder.objects.get(pk=2)

        self.assertFalse(order.reduction)
        self.assertEqual(len(Panier.objects.filter(user = self.user_2)), 0)

        data = {
            "tot_quantity": 2
        }
        self.client.post(reverse('commande:create-unique', kwargs={'slug': self.article.slug}), data)

        order = ValidatedOrder.objects.get(pk=3)

        self.assertTrue(order.reduction)



    def test_decrement_stock(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('commande:create'))
        self.assertEqual(response.status_code, 302)

        self.article.refresh_from_db()
        self.deuxieme_article.refresh_from_db()

        self.assertEqual(self.article.stock, 5)
        self.assertEqual(self.deuxieme_article.stock, 3)


    def test_create_unique_commande(self):

        self.client.force_login(self.user)

        data = {
            "tot_quantity": 9
        }
        response = self.client.post(reverse('commande:create-unique', kwargs={'slug': self.article.slug}), data)
        

        order = ValidatedOrder.objects.get(pk=1)
        
        self.assertTrue(order)
        self.assertEqual(order.tot_quantity, 9)
        self.assertEqual(order.tot_price, 22.5)
        self.assertEqual(order.user, self.user)
        self.assertFalse(order.reduction)

        ligne_order = LigneCommande.objects.filter(order=order)

        self.assertEqual(len(ligne_order), 1)
        self.assertEqual(ligne_order[0].article, self.article)
        self.assertEqual(ligne_order[0].price, self.article.price * 9)


class TestStatCommande(TestCase):

    def setUp(self):
        self.article = Article.objects.create(name='Article test', 
                                                published=0,
                                                price=2.5,
                                                stock=10,
                                                description="Une super description d'article",
                                                        )

        self.deuxieme_article = Article.objects.create(name='Deuxième article test', 
                                                published=0,
                                                price=6.99,
                                                stock=10,
                                                description="Une super description d'un deuxieme article",
                                                        )

        self.user = get_user_model().objects.create(first_name='name_test', 
                                                        username='test_1',
                                                        password='12test12',
                                                        email='test@example.com',
                                                        is_superuser=0)

        self.user_2 = get_user_model().objects.create(first_name='test_2', 
                                                        username='un autre nom 2',
                                                        password='12test123',
                                                        email='test_2@example.com',
                                                        is_superuser=1)
        
        Panier.objects.create(quantity=5, articles=self.article, user=self.user)
        Panier.objects.create(quantity=7, articles=self.deuxieme_article, user=self.user)

        Panier.objects.create(quantity=10, articles=self.article, user=self.user_2)
        Panier.objects.create(quantity=4, articles=self.deuxieme_article, user=self.user_2)

        self.panier = Panier.objects.filter(user = self.user)

        self.client.force_login(self.user)
        self.client.post(reverse('commande:create'))

        data = {
            "tot_quantity": 15
        }
        self.client.post(reverse('commande:create-unique', kwargs={'slug': self.article.slug}), data)

        self.client.force_login(self.user_2)
        self.client.post(reverse('commande:create'))

        data = {
            "tot_quantity": 25
        }
        self.client.post(reverse('commande:create-unique', kwargs={'slug': self.article.slug}), data)


    def test_shearch_order(self):
        self.client.force_login(self.user_2)
        
        response = self.client.get('/order/?q=autre')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['commande']), 2)
        self.assertEqual(len(response.context['commande'][1].articles.all()), 2)
        self.assertEqual(response.context['commande'][1].tot_quantity, 14)
        self.assertEqual(response.context['commande'][1].user, self.user_2)

        response = self.client.get('/order/?q=test_1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['commande']), 2)
        self.assertEqual(len(response.context['commande'][1].articles.all()), 2)
        self.assertEqual(response.context['commande'][1].tot_quantity, 12)
        self.assertEqual(response.context['commande'][1].user, self.user)


    def test_search_annee(self):
        self.client.force_login(self.user_2)
        
        response = self.client.get('/order/?q1=Année')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['commande']), 4)

        order = ValidatedOrder.objects.get(pk=1)
        order.created_on -= timedelta(days=400)
        order.save()

        response = self.client.get('/order/?q1=Année')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['commande']), 3)


    def test_search_month(self):
        self.client.force_login(self.user_2)
        
        response = self.client.get('/order/?q1=Mois')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['commande']), 4)

        order = ValidatedOrder.objects.get(pk=1)
        order.created_on -= timedelta(days=32)
        order.save()

        response = self.client.get('/order/?q1=Mois')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['commande']), 3)

    def test_search_month(self):
        self.client.force_login(self.user_2)
        
        response = self.client.get('/order/?q1=Jour')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['commande']), 4)

        order = ValidatedOrder.objects.get(pk=1)
        order.created_on -= timedelta(days=1)
        order.save()

        response = self.client.get('/order/?q1=Jour')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['commande']), 3)