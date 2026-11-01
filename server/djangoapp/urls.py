from django.urls import path
from . import views

app_name = 'djangoapp'
urlpatterns = [
    path('session', views.session_user, name='session'),
    path('login', views.login_user, name='login'),
    path('logout', views.logout_request, name='logout'),
    path('register', views.registration, name='register'),
    path('get_dealers', views.get_dealerships, name='get_dealers'),
    path('get_dealers/<str:state>', views.get_dealerships, name='dealers_by_state'),
    path('dealer/<int:dealer_id>', views.get_dealer_details, name='dealer'),
    path('reviews/dealer/<int:dealer_id>', views.get_dealer_reviews, name='reviews'),
    path('get_cars', views.get_cars, name='cars'),
    path('add_review', views.add_review, name='add_review'),
]
