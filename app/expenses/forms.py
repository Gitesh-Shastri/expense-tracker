from django import forms
from .models import Expense, Bank, Investment, Broker, InvestmentType, Category

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

class BankTransferForm(ExpenseForm):
    destination_bank = forms.ModelChoiceField(
        queryset=Bank.objects.none(),
        required=True,
        label='Destination Account'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set the source bank field label to make it clearer
        self.fields['bank'].label = 'Source Account'
        
        # Make transaction_type read-only as bank transfers always debit from source
        self.fields['transaction_type'].widget.attrs['readonly'] = True
        self.fields['transaction_type'].initial = 'DEBIT'
        
        # Only show Bank Transfer as category option
        try:
            bank_transfer_category = Category.objects.get(name='Bank Transfer')
            self.fields['category'].initial = bank_transfer_category
            self.fields['category'].widget.attrs['readonly'] = True
        except Category.DoesNotExist:
            pass
            
        # Set destination bank queryset
        if user:
            self.fields['destination_bank'].queryset = Bank.objects.filter(user=user)

    def clean(self):
        cleaned_data = super().clean()
        source_bank = cleaned_data.get('bank')
        destination_bank = cleaned_data.get('destination_bank')
        
        if source_bank and destination_bank:
            if source_bank == destination_bank:
                raise forms.ValidationError("Source and destination accounts cannot be the same.")
                
        return cleaned_data

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