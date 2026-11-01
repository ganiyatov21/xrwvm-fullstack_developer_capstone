import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.management import call_command
from .models import CarMake, CarModel


class PortalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('driver', password='A-Reliable-Password-2026', first_name='Test', last_name='Driver')
        call_command('seed_cars', verbosity=0)

    def post(self, path, data):
        return self.client.post('/djangoapp/' + path, json.dumps(data), content_type='application/json')

    def test_login_session_and_logout(self):
        response = self.post('login', {'userName': 'driver', 'password': 'incorrect'})
        self.assertEqual(response.status_code, 401)
        response = self.post('login', {'userName': 'driver', 'password': 'A-Reliable-Password-2026'})
        self.assertEqual(response.json()['status'], 'Authenticated')
        self.assertTrue(self.client.get('/djangoapp/session').json()['authenticated'])
        self.client.post('/djangoapp/logout')
        self.assertFalse(self.client.get('/djangoapp/session').json()['authenticated'])

    def test_csrf_is_enforced(self):
        response = Client(enforce_csrf_checks=True).post('/djangoapp/login', '{}', content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_registration_duplicate_and_weak_password(self):
        response = self.post('register', {'userName': 'newdriver', 'password': 'password'})
        self.assertEqual(response.status_code, 400)
        response = self.post('register', {'userName': 'newdriver', 'password': 'Another-Reliable-Pass-2026'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.get(username='newdriver').check_password('Another-Reliable-Pass-2026'))
        response = self.post('register', {'userName': 'newdriver', 'password': 'Another-Reliable-Pass-2026'})
        self.assertEqual(response.status_code, 409)

    def test_seed_is_idempotent(self):
        before = (CarMake.objects.count(), CarModel.objects.count())
        call_command('seed_cars', verbosity=0)
        self.assertEqual(before, (CarMake.objects.count(), CarModel.objects.count()))
        self.assertEqual(before, (5, 8))

    @patch('djangoapp.views.get_request', return_value=[{'id': 1, 'state': 'Kansas'}])
    def test_state_filter(self, remote):
        response = self.client.get('/djangoapp/get_dealers/Kansas')
        self.assertEqual(response.json()['dealers'][0]['state'], 'Kansas')
        remote.assert_called_once_with('fetchDealers/Kansas')

    @patch('djangoapp.views.analyze_review_sentiments', return_value='positive')
    @patch('djangoapp.views.get_request', return_value=[{'id': 1, 'review': 'Excellent service!'}])
    def test_review_sentiment(self, remote, analyze):
        self.assertEqual(self.client.get('/djangoapp/reviews/dealer/1').json()['reviews'][0]['sentiment'], 'positive')

    @patch('djangoapp.views.post_review', return_value={'id': 100})
    @patch('djangoapp.views.get_request', return_value=[{'id': 1}])
    def test_review_requires_login_and_uses_server_identity(self, remote, post_review):
        data = {'dealership': 1, 'review': 'Excellent service.', 'name': 'Forged Identity', 'purchase_date': '2023-06-15', 'car_make': 'Toyota', 'car_model': 'Camry', 'car_year': 2023}
        self.assertEqual(self.post('add_review', data).status_code, 401)
        self.client.force_login(self.user)
        self.assertEqual(self.post('add_review', data).status_code, 201)
        self.assertEqual(post_review.call_args.args[0]['name'], 'Test Driver')
        data['car_year'] = 1900
        self.assertEqual(self.post('add_review', data).status_code, 400)
