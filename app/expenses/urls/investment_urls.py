from django.urls import path
from expenses.views.investment.views import (
    # Investment views
    InvestmentListView,
    InvestmentCreateView,
    InvestmentUpdateView,
    InvestmentDeleteView,
    # Broker views
    BrokerListView,
    BrokerCreateView,
    BrokerUpdateView,
    BrokerDeleteView,
    # Investment Type views
    InvestmentTypeListView,
    InvestmentTypeCreateView,
    InvestmentTypeUpdateView,
    InvestmentTypeDeleteView
)

app_name = 'investments'

urlpatterns = [
    # Investment URLs
    path('', InvestmentListView.as_view(), name='investment_list'),
    path('create/', InvestmentCreateView.as_view(), name='investment_create'),
    path('<int:pk>/edit/', InvestmentUpdateView.as_view(), name='investment_edit'),
    path('<int:pk>/delete/', InvestmentDeleteView.as_view(), name='investment_delete'),
    
    # Broker URLs
    path('brokers/', BrokerListView.as_view(), name='broker_list'),
    path('brokers/create/', BrokerCreateView.as_view(), name='broker_create'),
    path('brokers/<int:pk>/edit/', BrokerUpdateView.as_view(), name='broker_edit'),
    path('brokers/<int:pk>/delete/', BrokerDeleteView.as_view(), name='broker_delete'),
    
    # Investment Type URLs
    path('types/', InvestmentTypeListView.as_view(), name='investment_type_list'),
    path('types/create/', InvestmentTypeCreateView.as_view(), name='investment_type_create'),
    path('types/<int:pk>/edit/', InvestmentTypeUpdateView.as_view(), name='investment_type_edit'),
    path('types/<int:pk>/delete/', InvestmentTypeDeleteView.as_view(), name='investment_type_delete'),
]