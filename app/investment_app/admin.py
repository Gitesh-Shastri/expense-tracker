from django.contrib import admin
from expenses.models import Investment, Broker, InvestmentType

@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'investment_type', 'broker', 'amount', 'purchase_date', 'status', 'user')
    list_filter = ('status', 'investment_type', 'broker', 'user')
    search_fields = ('name', 'broker__name', 'investment_type__name')
    date_hierarchy = 'purchase_date'

@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_number', 'user')
    list_filter = ('user',)
    search_fields = ('name', 'account_number')

@admin.register(InvestmentType)
class InvestmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'risk_level')
    list_filter = ('risk_level',)
    search_fields = ('name',)
