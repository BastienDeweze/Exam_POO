from django.contrib.auth.models import User
from django.contrib.auth import SESSION_KEY
from django.http import response
from django.test import TestCase
from django.test import Client
from django.urls import reverse
from .models import UserProfile
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from .forms import UserRegisterForm

class TestAuth(TestCase):
    def setUp(self):
        self.form_data = {
            "password1": "Adedfsfd!123",
            "password2": "Adedfsfd!123",
            "first_name": "bass",
            "email": "bass@yahoo.com",
            'username': 'bass'
        }
    def test_form_register(self):
        
        form = UserRegisterForm(self.form_data)
        self.assertTrue(form.is_valid)

    def test_register(self):
        
        response = self.client.post('/account/signup/', data=self.form_data)
        self.assertTrue(get_user_model().objects.filter(username='bass').exists())
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username='bass')
        self.assertEqual(user.email, "bass@yahoo.com")

    def test(self):
        u = User.objects.create(username="bas", password = "sdbfdsgdfqd!123", email="blebla@gmail.com")
        payload = {
            "password": "sdbfdsgdfqd!123",
            "username": "bas"
        }

        # login
        response = self.client.post('/account/login/', data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(u.is_authenticated)

class TestProfile(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(first_name='name_test', 
                                                        username='test',
                                                        password='12test12',
                                                        email='test@example.com')
        self.us = UserProfile.objects.get(user=self.user)


    def test_detail_profile(self):
        response = self.client.get('/account/test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, ['account/profile.html'])
        self.assertTrue(response.context['userprofile'])
        self.assertTrue(response.context['userprofile'].slug, 'test')
        self.assertTrue(response.context['userprofile'].reduction_threshold, 10)
        self.assertTrue(response.context['userprofile'].first_name, 'name_test')
        self.assertTrue(response.context['userprofile'].city, "0000")
        self.assertTrue(response.context['userprofile'].user.email, 'test@example.com')

    def test_update_profile(self):

        data = {'first_name' : 'test_update', 'last_name' : 'Bastien',  'city' : '4040'}

        response = self.client.post(reverse('account:edit', kwargs={'slug': 'test'}), data)

        self.assertEqual(response.status_code, 302)
        self.us.refresh_from_db()

        self.assertTrue(self.us)
        self.assertTrue(self.us.slug, 'test')
        self.assertTrue(self.us.reduction_threshold, 10)
        self.assertTrue(self.us.first_name, 'test_update')
        self.assertTrue(self.us.last_name, 'Bastien')
        self.assertTrue(self.us.city, "4040")
        self.assertTrue(self.us.user.email, 'test@example.com')

    def test_delete_user(self):
        self.us.delete()
        self.assertFalse(UserProfile.objects.filter(user=self.user).exists())
        self.assertFalse(get_user_model().objects.filter(pk=self.user.id).exists())
        
    # def test_shearch_profile(self):
    #     response = self.client.get('/account/?q=test/')
    #     print(response.__dict__)