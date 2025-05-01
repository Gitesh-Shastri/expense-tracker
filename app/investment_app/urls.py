from django.urls import path
from . import views

app_name = 'investment_app'

urlpatterns = [
    # Investment URLs
    path('', views.InvestmentListView.as_view(), name='investment_list'),
    path('create/', views.InvestmentCreateView.as_view(), name='investment_create'),
    path('<int:pk>/edit/', views.InvestmentUpdateView.as_view(), name='investment_edit'),
    path('<int:pk>/delete/', views.InvestmentDeleteView.as_view(), name='investment_delete'),
    
    # Broker URLs
    path('brokers/', views.BrokerListView.as_view(), name='broker_list'),
    path('brokers/create/', views.BrokerCreateView.as_view(), name='broker_create'),
    path('brokers/<int:pk>/edit/', views.BrokerUpdateView.as_view(), name='broker_edit'),
    path('brokers/<int:pk>/delete/', views.BrokerDeleteView.as_view(), name='broker_delete'),
    
    # Investment Type URLs
    path('types/', views.InvestmentTypeListView.as_view(), name='investment_type_list'),
    path('types/create/', views.InvestmentTypeCreateView.as_view(), name='investment_type_create'),
    path('types/<int:pk>/edit/', views.InvestmentTypeUpdateView.as_view(), name='investment_type_edit'),
    path('types/<int:pk>/delete/', views.InvestmentTypeDeleteView.as_view(), name='investment_type_delete'),
]