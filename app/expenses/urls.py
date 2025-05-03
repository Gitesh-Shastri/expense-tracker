from django.urls import path
from .views import (
    MonthlyExpenseView,
    ExpenseCreateView,
    ExpenseUpdateView,
    ExpenseDeleteView,
    BankTransferCreateView,
)

app_name = 'expenses'

urlpatterns = [
    path('', MonthlyExpenseView.as_view(), name='monthly_expenses'),
    path('create/', ExpenseCreateView.as_view(), name='expense_create'),
    path('bank-transfer/', BankTransferCreateView.as_view(), name='bank_transfer'),
    path('<int:pk>/edit/', ExpenseUpdateView.as_view(), name='expense_edit'),
    path('<int:pk>/delete/', ExpenseDeleteView.as_view(), name='expense_delete'),
]