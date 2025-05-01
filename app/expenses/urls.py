from django.urls import path
from views import home

app_name = 'expenses'

urlpatterns = [
    # Home page
    path('home/', home, name='home'),
]