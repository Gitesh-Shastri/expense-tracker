from django import forms
from .models import Expense, Bank, Investment, Broker, InvestmentType

class ExpenseForm(forms.ModelForm):
    opening_balance = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        initial=0.00,
        label='Opening Balance',
        help_text='Set the initial balance for this bank account'
    )

    class Meta:
        model = Expense
        fields = ['amount', 'description', 'category', 'bank', 'transaction_type', 'date', 'opening_balance']

    def clean_opening_balance(self):
        opening_balance = self.cleaned_data.get('opening_balance')
        if opening_balance is not None and opening_balance < 0:
            raise forms.ValidationError("Opening balance cannot be negative")
        return opening_balance

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance

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
            'broker', 'investment_type', 'name', 'amount', 'units', 
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