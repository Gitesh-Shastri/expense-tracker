from django.urls import path
from .views import (
    MonthlyExpenseView,
    ExpenseCreateView,
    ExpenseUpdateView,
    ExpenseDeleteView,
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
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', MonthlyExpenseView.as_view(), name='monthly_expenses'),
    path('create/', ExpenseCreateView.as_view(), name='expense_create'),
    path('<int:pk>/edit/', ExpenseUpdateView.as_view(), name='expense_edit'),
    path('<int:pk>/delete/', ExpenseDeleteView.as_view(), name='expense_delete'),
    
    # EMI URLs
    path('emi/', views.EMIListView.as_view(), name='emi_list'),
    path('emi/create/', views.EMICreateView.as_view(), name='emi_create'),
    path('emi/<int:pk>/edit/', views.EMIUpdateView.as_view(), name='emi_edit'),
    path('emi/<int:pk>/delete/', views.EMIDeleteView.as_view(), name='emi_delete'),
    path('emi/<int:pk>/mark-paid/', views.mark_emi_as_paid, name='emi_mark_paid'),
    
    # Investment URLs
    path('investments/', InvestmentListView.as_view(), name='investment_list'),
    path('investments/create/', InvestmentCreateView.as_view(), name='investment_create'),
    path('investments/<int:pk>/edit/', InvestmentUpdateView.as_view(), name='investment_edit'),
    path('investments/<int:pk>/delete/', InvestmentDeleteView.as_view(), name='investment_delete'),
    
    # Broker URLs
    path('brokers/', BrokerListView.as_view(), name='broker_list'),
    path('brokers/create/', BrokerCreateView.as_view(), name='broker_create'),
    path('brokers/<int:pk>/edit/', BrokerUpdateView.as_view(), name='broker_edit'),
    path('brokers/<int:pk>/delete/', BrokerDeleteView.as_view(), name='broker_delete'),
    
    # Investment Type URLs
    path('investment-types/', InvestmentTypeListView.as_view(), name='investment_type_list'),
    path('investment-types/create/', InvestmentTypeCreateView.as_view(), name='investment_type_create'),
    path('investment-types/<int:pk>/edit/', InvestmentTypeUpdateView.as_view(), name='investment_type_edit'),
    path('investment-types/<int:pk>/delete/', InvestmentTypeDeleteView.as_view(), name='investment_type_delete'),
]