from django import forms
from expenses.models import Investment, Broker, InvestmentType

class BrokerForm(forms.ModelForm):
    class Meta:
        model = Broker
        fields = ['name', 'account_number', 'description', 'website']
        
class InvestmentTypeForm(forms.ModelForm):
    class Meta:
        model = InvestmentType
        fields = ['name', 'description', 'risk_level']
        
class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = [
            'broker', 'investment_type', 'name', 'amount', 'currency', 'units', 
            'purchase_price', 'current_price', 'purchase_date', 
            'transaction_type', 'status', 'maturity_date', 'notes'
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'maturity_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['broker'].queryset = Broker.objects.filter(user=user)