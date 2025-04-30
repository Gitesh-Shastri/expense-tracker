from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Sum, Count
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .models import Expense, Category, Bank, EMI, Investment, Broker, InvestmentType
from .forms import ExpenseForm, BrokerForm, InvestmentTypeForm, InvestmentForm
from datetime import datetime, timedelta

# Create your views here.

class MonthlyExpenseView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'expenses/monthly_expenses.html'
    context_object_name = 'expenses'

    def get_queryset(self):
        # Get the month from URL parameter or use current month
        month_str = self.request.GET.get('month')
        if month_str:
            month = datetime.strptime(month_str, '%Y-%m')
        else:
            month = timezone.now().replace(day=1)

        # Set the month in the view
        self.month = month

        # Get expenses for the selected month, ordered by date
        return Expense.objects.filter(
            user=self.request.user,
            date__year=month.year,
            date__month=month.month
        ).select_related('category', 'bank').order_by('date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add month information
        context['month'] = self.month
        context['prev_month'] = self.month - timedelta(days=1)
        context['next_month'] = (self.month.replace(day=28) + timedelta(days=4)).replace(day=1)

        # Calculate totals
        expenses = self.get_queryset()
        debit_expenses = expenses.filter(transaction_type='DEBIT')
        credit_expenses = expenses.filter(transaction_type='CREDIT')

        context['total_expenses'] = debit_expenses.aggregate(total=Sum('amount'))['total'] or 0
        context['total_income'] = credit_expenses.aggregate(total=Sum('amount'))['total'] or 0
        context['total_opening_balance'] = expenses.aggregate(total=Sum('opening_balance'))['total'] or 0
        context['balance'] = context['total_income'] - context['total_expenses'] + context['total_opening_balance']
        context['transactions_count'] = expenses.count()

        # Category-wise breakdown
        category_breakdown = []
        for category in Category.objects.all():
            category_expenses = expenses.filter(category=category)
            debit = category_expenses.filter(transaction_type='DEBIT').aggregate(total=Sum('amount'))['total'] or 0
            credit = category_expenses.filter(transaction_type='CREDIT').aggregate(total=Sum('amount'))['total'] or 0
            total = debit + credit
            if total > 0:
                percentage = (total / context['total_expenses'] * 100) if context['total_expenses'] > 0 else 0
                category_breakdown.append({
                    'category': category,
                    'debit': debit,
                    'credit': credit,
                    'total': total,
                    'percentage': round(percentage, 1),
                    'count': category_expenses.count()
                })
        
        # Sort by total amount
        context['category_breakdown'] = sorted(category_breakdown, key=lambda x: x['total'], reverse=True)

        # Bank-wise summary and transactions
        bank_transactions = {}
        bank_summary = []
        for bank in Bank.objects.filter(user=self.request.user):
            # Get all transactions for this bank up to the current month
            all_bank_expenses = Expense.objects.filter(
                user=self.request.user,
                bank=bank,
                date__lte=self.month.replace(day=1) + timedelta(days=32)
            ).order_by('date')
            
            # Get opening balance from the first expense record
            opening_balance = all_bank_expenses.aggregate(
                opening=Sum('opening_balance')
            )['opening'] or 0
            
            # Get current month's transactions
            bank_expenses = expenses.filter(bank=bank)
            bank_debit = debit_expenses.filter(bank=bank).aggregate(total=Sum('amount'))['total'] or 0
            bank_credit = credit_expenses.filter(bank=bank).aggregate(total=Sum('amount'))['total'] or 0
            
            # Calculate total debit and credit up to current month
            total_debit = all_bank_expenses.filter(transaction_type='DEBIT').aggregate(total=Sum('amount'))['total'] or 0
            total_credit = all_bank_expenses.filter(transaction_type='CREDIT').aggregate(total=Sum('amount'))['total'] or 0
            
            # Calculate current balance (opening balance + total credits - total debits)
            current_balance = opening_balance + total_credit - total_debit
            
            bank_summary.append({
                'bank': bank,
                'opening_balance': opening_balance,
                'debit': bank_debit,
                'credit': bank_credit,
                'balance': current_balance
            })
            
            bank_transactions[bank.id] = {
                'bank': bank,
                'opening_balance': opening_balance,
                'current_balance': current_balance,
                'transactions': bank_expenses
            }
        
        context['bank_summary'] = bank_summary
        context['bank_transactions'] = bank_transactions

        return context

class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    template_name = 'expenses/expense_form.html'
    form_class = ExpenseForm
    success_url = reverse_lazy('expenses:monthly_expenses')

    def form_valid(self, form):
        form.instance.user = self.request.user
        # Get the opening balance from the form
        opening_balance = form.cleaned_data.get('opening_balance')
        if opening_balance is not None:
            # Update the bank's opening balance and current balance
            bank = form.cleaned_data.get('bank')
            bank.opening_balance = opening_balance
            bank.balance = opening_balance
            bank.save()
        response = super().form_valid(form)
        
        # If "Save and Add Another" was clicked, redirect to create form with previous values
        if 'save_and_add' in self.request.POST:
            # Create URL with all form values as parameters
            params = {
                'bank': form.cleaned_data.get('bank').id,
                'amount': form.cleaned_data.get('amount'),
                'description': form.cleaned_data.get('description'),
                'category': form.cleaned_data.get('category').id if form.cleaned_data.get('category') else '',
                'transaction_type': form.cleaned_data.get('transaction_type'),
                'date': form.cleaned_data.get('date').strftime('%Y-%m-%d') if form.cleaned_data.get('date') else '',
                'opening_balance': opening_balance,
            }
            # Filter out empty values
            params = {k: v for k, v in params.items() if v}
            # Create query string
            query_string = '&'.join(f"{k}={v}" for k, v in params.items())
            return redirect(f"{reverse('expenses:expense_create')}?{query_string}")
            
        return response

    def get_initial(self):
        initial = super().get_initial()
        
        # Get all parameters from URL
        bank_id = self.request.GET.get('bank')
        if bank_id:
            try:
                bank = Bank.objects.get(id=bank_id, user=self.request.user)
                initial['bank'] = bank
            except Bank.DoesNotExist:
                pass
        
        # Handle category
        category_id = self.request.GET.get('category')
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                initial['category'] = category
            except Category.DoesNotExist:
                pass
        
        # Update initial with other form values from URL
        initial.update({
            'amount': self.request.GET.get('amount'),
            'description': self.request.GET.get('description'),
            'transaction_type': self.request.GET.get('transaction_type'),
            'date': self.request.GET.get('date'),
            'opening_balance': self.request.GET.get('opening_balance'),
        })
        
        # Remove None values
        initial = {k: v for k, v in initial.items() if v is not None}
            
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['banks'] = Bank.objects.filter(user=self.request.user)
        return context

class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    template_name = 'expenses/expense_form.html'
    form_class = ExpenseForm
    success_url = reverse_lazy('expenses:monthly_expenses')

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['banks'] = Bank.objects.filter(user=self.request.user)
        return context

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses:monthly_expenses')

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)

class EMIListView(LoginRequiredMixin, ListView):
    model = EMI
    template_name = 'expenses/emi_list.html'
    context_object_name = 'emis'

    def get_queryset(self):
        # Get the month from URL parameter or use current month
        month_str = self.request.GET.get('month')
        if month_str:
            month = datetime.strptime(month_str, '%Y-%m')
        else:
            month = timezone.now().replace(day=1)

        # Set the month in the view
        self.month = month

        return EMI.objects.filter(user=self.request.user).order_by('due_date_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add month information for navigation
        context['month'] = self.month
        context['prev_month'] = self.month - timedelta(days=1)
        context['next_month'] = (self.month.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        # Get current month's paid EMIs
        current_month_paid_emis = self.get_queryset().filter(
            status='PAID',
            due_date_time__year=self.month.year,
            due_date_time__month=self.month.month
        ).order_by('-due_date_time')
        
        # Get all pending EMIs for the selected month
        pending_emis = self.get_queryset().filter(
            status='PENDING',
            due_date_time__year=self.month.year,
            due_date_time__month=self.month.month
        )
        
        # Calculate totals
        pending_total = pending_emis.aggregate(total=Sum('amount'))['total'] or 0
        paid_total = current_month_paid_emis.aggregate(total=Sum('amount'))['total'] or 0
        
        context.update({
            'pending_emis': pending_emis,
            'paid_emis': current_month_paid_emis,
            'pending_total': pending_total,
            'paid_total': paid_total,
            'today': timezone.now(),
        })
        
        return context

class EMICreateView(LoginRequiredMixin, CreateView):
    model = EMI
    template_name = 'expenses/emi_form.html'
    fields = ['bank', 'amount', 'description', 'category', 'start_date', 'end_date', 'due_date_time']
    success_url = reverse_lazy('expenses:emi_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banks'] = Bank.objects.filter(user=self.request.user)
        context['categories'] = Category.objects.all()
        return context

class EMIUpdateView(LoginRequiredMixin, UpdateView):
    model = EMI
    template_name = 'expenses/emi_form.html'
    fields = ['bank', 'amount', 'description', 'category', 'start_date', 'end_date', 'due_date_time', 'status']
    success_url = reverse_lazy('expenses:emi_list')

    def get_queryset(self):
        return EMI.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banks'] = Bank.objects.filter(user=self.request.user)
        context['categories'] = Category.objects.all()
        return context

class EMIDeleteView(LoginRequiredMixin, DeleteView):
    model = EMI
    template_name = 'expenses/emi_confirm_delete.html'
    success_url = reverse_lazy('expenses:emi_list')

    def get_queryset(self):
        return EMI.objects.filter(user=self.request.user)

def mark_emi_as_paid(request, pk):
    if request.method == 'POST':
        try:
            emi = EMI.objects.get(pk=pk, user=request.user)
            emi.mark_as_paid()
            return JsonResponse({'status': 'success'})
        except EMI.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'EMI not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

# Investment Views
class InvestmentListView(LoginRequiredMixin, ListView):
    model = Investment
    template_name = 'expenses/investment_list.html'
    context_object_name = 'investments'

    def get_queryset(self):
        return Investment.objects.filter(user=self.request.user).order_by('-purchase_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active investments
        active_investments = self.get_queryset().filter(status='ACTIVE')
        
        # Calculate investment summary
        total_invested = active_investments.aggregate(total=Sum('amount'))['total'] or 0
        total_value = sum((inv.current_price * inv.units) for inv in active_investments)
        total_profit_loss = active_investments.aggregate(total=Sum('profit_loss'))['total'] or 0
        
        # Group investments by type
        investment_types = {}
        for investment_type in InvestmentType.objects.all():
            type_investments = active_investments.filter(investment_type=investment_type)
            if type_investments:
                type_amount = type_investments.aggregate(total=Sum('amount'))['total'] or 0
                type_current_value = sum((inv.current_price * inv.units) for inv in type_investments)
                type_profit_loss = type_investments.aggregate(total=Sum('profit_loss'))['total'] or 0
                
                investment_types[investment_type.id] = {
                    'name': investment_type.name,
                    'amount': type_amount,
                    'current_value': type_current_value,
                    'profit_loss': type_profit_loss,
                    'count': type_investments.count()
                }
        
        # Group investments by broker
        brokers = {}
        for broker in Broker.objects.filter(user=self.request.user):
            broker_investments = active_investments.filter(broker=broker)
            if broker_investments:
                broker_amount = broker_investments.aggregate(total=Sum('amount'))['total'] or 0
                broker_current_value = sum((inv.current_price * inv.units) for inv in broker_investments)
                broker_profit_loss = broker_investments.aggregate(total=Sum('profit_loss'))['total'] or 0
                
                brokers[broker.id] = {
                    'name': broker.name,
                    'amount': broker_amount,
                    'current_value': broker_current_value,
                    'profit_loss': broker_profit_loss,
                    'count': broker_investments.count()
                }
        
        context.update({
            'active_investments': active_investments,
            'closed_investments': self.get_queryset().filter(status='CLOSED'),
            'total_invested': total_invested,
            'total_value': total_value,
            'total_profit_loss': total_profit_loss,
            'investment_types': investment_types,
            'brokers': brokers
        })
        
        return context

class InvestmentCreateView(LoginRequiredMixin, CreateView):
    model = Investment
    template_name = 'expenses/investment_form.html'
    form_class = InvestmentForm
    success_url = reverse_lazy('expenses:investment_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['investment_types'] = InvestmentType.objects.all()
        return context

class InvestmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Investment
    template_name = 'expenses/investment_form.html'
    form_class = InvestmentForm
    success_url = reverse_lazy('expenses:investment_list')

    def get_queryset(self):
        return Investment.objects.filter(user=self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['investment_types'] = InvestmentType.objects.all()
        return context

class InvestmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Investment
    template_name = 'expenses/investment_confirm_delete.html'
    success_url = reverse_lazy('expenses:investment_list')

    def get_queryset(self):
        return Investment.objects.filter(user=self.request.user)

# Broker Views
class BrokerListView(LoginRequiredMixin, ListView):
    model = Broker
    template_name = 'expenses/broker_list.html'
    context_object_name = 'brokers'

    def get_queryset(self):
        return Broker.objects.filter(user=self.request.user).order_by('name')

class BrokerCreateView(LoginRequiredMixin, CreateView):
    model = Broker
    form_class = BrokerForm
    template_name = 'expenses/broker_form.html'
    success_url = reverse_lazy('expenses:broker_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class BrokerUpdateView(LoginRequiredMixin, UpdateView):
    model = Broker
    form_class = BrokerForm
    template_name = 'expenses/broker_form.html'
    success_url = reverse_lazy('expenses:broker_list')

    def get_queryset(self):
        return Broker.objects.filter(user=self.request.user)

class BrokerDeleteView(LoginRequiredMixin, DeleteView):
    model = Broker
    template_name = 'expenses/broker_confirm_delete.html'
    success_url = reverse_lazy('expenses:broker_list')

    def get_queryset(self):
        return Broker.objects.filter(user=self.request.user)

# Investment Type Views
class InvestmentTypeListView(LoginRequiredMixin, ListView):
    model = InvestmentType
    template_name = 'expenses/investment_type_list.html'
    context_object_name = 'investment_types'

    def get_queryset(self):
        return InvestmentType.objects.all().order_by('name')

class InvestmentTypeCreateView(LoginRequiredMixin, CreateView):
    model = InvestmentType
    form_class = InvestmentTypeForm
    template_name = 'expenses/investment_type_form.html'
    success_url = reverse_lazy('expenses:investment_type_list')

class InvestmentTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = InvestmentType
    form_class = InvestmentTypeForm
    template_name = 'expenses/investment_type_form.html'
    success_url = reverse_lazy('expenses:investment_type_list')

class InvestmentTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = InvestmentType
    template_name = 'expenses/investment_type_confirm_delete.html'
    success_url = reverse_lazy('expenses:investment_type_list')
