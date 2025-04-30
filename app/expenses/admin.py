from django.contrib import admin
from .models import Bank, Category, Expense, EMI
# Register your models here.

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('amount', 'date', 'description', 'category', 'bank')
    list_filter = ('category', 'bank')
    search_fields = ('description',)

class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_number', 'account_type')
    search_fields = ('name',)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class EMIAdmin(admin.ModelAdmin):
    list_display = ('amount', 'description', 'category', 'end_date', 'due_date_time', 'status')
    list_filter = ('description', 'status')
    search_fields = ('description',)

admin.site.register(Bank, BankAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(EMI, EMIAdmin)