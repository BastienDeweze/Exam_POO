from django.test import TestCase
from .models import Article, Category
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models import Q


class TestArticles(TestCase):

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
                                                        is_superuser=1)

        self.category = Category.objects.create(name="Nom cat", description="Description cat")

    def test_detail_article(self):
        response = self.client.get('/articles/article-test')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, ['articles/article_detail.html'])
        self.assertTrue(response.context['article'])
        self.assertTrue(response.context['article'].slug, 'article-test')
        self.assertFalse(response.context['article'].published)
        self.assertEqual(response.context['article'].name, 'Article test')
        self.assertEqual(response.context['article'].stock, 0)
        self.assertEqual(response.context['article'].price, 2.5)

    def test_update_article(self):
        self.client.force_login(self.user)

        data = {'name' : 'test_update',  
                    'description' : "Une super description update", 
                    'published': True,
                    "price": 5.99, 
                    "categories": ["1"],
                    "stock":6
                    }

        response = self.client.post(reverse('articles:edit', kwargs={'slug': self.article.slug}), data)
        
        self.article.refresh_from_db()
        self.assertEqual(response.status_code, 302)

        self.assertTrue(self.article)
        self.assertEqual(self.article.slug, 'article-test')
        self.assertEqual(self.article.name, 'test_update')
        self.assertEqual(self.article.description, 'Une super description update')
        self.assertEqual(self.article.price, data['price'])
        self.assertTrue(self.article.published)
        self.assertEqual(self.article.stock, 6)

    def test_create_article(self):
        self.client.force_login(self.user)
        data = {'name' : 'test_create',  
                    'description' : "Une super description créé", 
                    "price": 10.99, 
                    "categories": ["1"],
                    }

        response = self.client.post(reverse('articles:create'), data)

        print(response)
        
        self.allArticle = Article.objects.all()
        print(self.allArticle.get(id=2).price)


        self.assertEqual(response.status_code, 302)

        self.assertEqual(len(self.allArticle[1].categories.all()), 1)
        self.assertTrue(self.allArticle)
        self.assertEqual(len(self.allArticle), 2)
        self.assertEqual(self.allArticle[1].name, 'test_create')

    def test_delete_articles(self):
        self.client.force_login(self.user)
        lenQueryset = len(Article.objects.all())
        slug = self.article.slug
        response = self.client.post(reverse('articles:delete', kwargs={'slug': self.article.slug}))
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(Article.objects.all()), lenQueryset - 1)
        self.assertFalse(Article.objects.filter(slug=slug).exists())

    def test_shearch_articles(self):
        self.article = Article.objects.create(name='Article test à trouver', 
                                                published=1,
                                                price=4.99,
                                                description="Une super description d'article à trouver",
                                                        )

        self.article2 = Article.objects.create(name='Article test à trouver impérativement', 
                                                published=1,
                                                price=4.99,
                                                description="Une super description d'article à trouver",
                                                        )
        
        response = self.client.get('/articles/?q=impérativement')
        self.assertEqual(len(response.context['articles']), 1)
        self.assertEqual(response.context['articles'][0].name, self.article2.name)
        self.assertEqual(response.status_code, 200)

        response2 = self.client.get('/articles/?q=rouver')
        self.assertEqual(len(response2.context['articles']), 2)
        self.assertEqual(response2.context['articles'][0].name, self.article.name)
        self.assertEqual(response2.context['articles'][1].name, self.article2.name)
        self.assertEqual(response2.status_code, 200)