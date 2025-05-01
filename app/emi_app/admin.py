from django.contrib import admin
from expenses.models import EMI

@admin.register(EMI)
class EMIAdmin(admin.ModelAdmin):
    list_display = ('description', 'bank', 'amount', 'due_date_time', 'status', 'user')
    list_filter = ('status', 'bank', 'user')
    search_fields = ('description', 'bank__name')
    date_hierarchy = 'due_date_time'
