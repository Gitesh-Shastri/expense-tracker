from django.shortcuts import redirect, render
from django.utils import timezone
from django.db.models import Sum
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Expense, Category, Bank
from .forms import ExpenseForm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class MonthlyExpenseView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'expenses/expense/monthly_expenses.html'
    context_object_name = 'expenses'

    def get_queryset(self):
        # Get the month from URL parameter or use current month
        month_str = self.request.GET.get('month')
        if month_str:
            # Create timezone-aware datetime object
            naive_month = datetime.strptime(month_str, '%Y-%m')
            month = timezone.make_aware(
                naive_month, 
                timezone.get_current_timezone()
            )
        else:
            # Use Django's timezone-aware now
            month = timezone.localtime(timezone.now()).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

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
        
        # Add month information - use timezone-aware arithmetic
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
                date__lt=self.month.replace(day=1) + relativedelta(months=1),
                date__gte=self.month.replace(day=1)
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
    template_name = 'expenses/expense/expense_form.html'
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
    template_name = 'expenses/expense/expense_form.html'
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
    template_name = 'expenses/expense/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses:monthly_expenses')

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)