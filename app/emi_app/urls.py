from django.urls import path
from .views import (
    EMIListView,
    EMICreateView,
    EMIUpdateView,
    EMIDeleteView,
    mark_emi_as_paid
)

app_name = 'emi_app'

urlpatterns = [
    path('', EMIListView.as_view(), name='emi_list'),
    path('create/', EMICreateView.as_view(), name='emi_create'),
    path('<int:pk>/edit/', EMIUpdateView.as_view(), name='emi_edit'),
    path('<int:pk>/delete/', EMIDeleteView.as_view(), name='emi_delete'),
    path('<int:pk>/mark-paid/', mark_emi_as_paid, name='emi_mark_paid'),
]