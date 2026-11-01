import json
from datetime import date
from functools import wraps
from urllib.parse import quote
import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from .models import CarModel
from .restapis import get_request, analyze_review_sentiments, post_review

def api_errors(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, ValueError) as error:
            return JsonResponse({'status': 400, 'error': str(error)}, status=400)
        except requests.RequestException:
            return JsonResponse({'status': 503, 'error': 'A backend service is unavailable. Please try again.'}, status=503)
    return wrapped

@require_GET
@ensure_csrf_cookie
def session_user(request):
    user = request.user
    return JsonResponse({'authenticated': user.is_authenticated, 'userName': user.username if user.is_authenticated else '', 'firstName': user.first_name if user.is_authenticated else '', 'lastName': user.last_name if user.is_authenticated else ''})

@require_POST
@api_errors
def login_user(request):
    data = json.loads(request.body)
    user = authenticate(request, username=data['userName'], password=data['password'])
    if user is None:
        return JsonResponse({'status': 'Invalid credentials', 'error': 'Invalid username or password.'}, status=401)
    login(request, user)
    return JsonResponse({'status': 'Authenticated', 'userName': user.username})

@require_POST
def logout_request(request):
    logout(request)
    return JsonResponse({'status': 200})

@require_POST
@api_errors
def registration(request):
    data = json.loads(request.body)
    username = data['userName'].strip()
    if not username or len(username) > 150:
        raise ValueError('A username of 1–150 characters is required.')
    user = User(username=username, first_name=data.get('firstName', '').strip(), last_name=data.get('lastName', '').strip(), email=data.get('email', '').strip())
    try:
        validate_password(data['password'], user=user)
        user.set_password(data['password'])
        user.save()
    except ValidationError as error:
        return JsonResponse({'error': ' '.join(error.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({'error': 'This username is already registered.'}, status=409)
    login(request, user)
    return JsonResponse({'status': 'Authenticated', 'userName': user.username}, status=201)

@require_GET
@api_errors
def get_dealerships(request, state='All'):
    endpoint = 'fetchDealers' if state == 'All' else f'fetchDealers/{quote(state, safe="")}'
    return JsonResponse({'status': 200, 'dealers': get_request(endpoint)})

@require_GET
@api_errors
def get_dealer_details(request, dealer_id):
    dealers = get_request(f'fetchDealer/{dealer_id}')
    return JsonResponse({'status': 200 if dealers else 404, 'dealer': dealers}, status=200 if dealers else 404)

@require_GET
@api_errors
def get_dealer_reviews(request, dealer_id):
    reviews = get_request(f'fetchReviews/dealer/{dealer_id}')
    for review in reviews:
        review['sentiment'] = analyze_review_sentiments(review['review'])
    return JsonResponse({'status': 200, 'reviews': reviews})

@require_GET
def get_cars(request):
    models = [{'id': car.id, 'CarMake': car.car_make.name, 'CarModel': car.name, 'CarYear': car.year} for car in CarModel.objects.select_related('car_make').all()]
    return JsonResponse({'status': 200, 'CarModels': models})

@require_POST
@api_errors
def add_review(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please log in before posting a review.'}, status=401)
    data = json.loads(request.body)
    dealer_id = int(data['dealership'])
    if not get_request(f'fetchDealer/{dealer_id}'):
        return JsonResponse({'error': 'Dealer not found.'}, status=404)
    text = data['review'].strip()
    if not text or len(text) > 5000:
        raise ValueError('Review must contain 1–5000 characters.')
    year = int(data['car_year'])
    if not 2015 <= year <= date.today().year:
        raise ValueError('Choose a valid car year.')
    if not CarModel.objects.filter(car_make__name=data['car_make'], name=data['car_model']).exists():
        raise ValueError('Choose a car from the inventory.')
    purchase_date = date.fromisoformat(data['purchase_date'])
    if purchase_date > date.today():
        raise ValueError('Purchase date cannot be in the future.')
    payload = {key: data[key] for key in ('car_make', 'car_model')}
    payload.update(name=request.user.get_full_name() or request.user.username, dealership=dealer_id, review=text, purchase=bool(data.get('purchase', True)), purchase_date=purchase_date.isoformat(), car_year=year)
    saved = post_review(payload)
    return JsonResponse({'status': 200, 'review': saved}, status=201)
