from django.db.models import Sum
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from expenses.models import Investment, InvestmentType, Broker
from .forms import InvestmentForm, BrokerForm, InvestmentTypeForm
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal


class InvestmentListView(LoginRequiredMixin, ListView):
    model = Investment
    template_name = 'investment_app/investment_list.html'
    context_object_name = 'investments'

    def get_queryset(self):
        # Get the selected month from the query parameters or use the current month
        month_str = self.request.GET.get('month')
        if month_str:
            selected_month = datetime.strptime(month_str, '%Y-%m')
        else:
            selected_month = timezone.now().replace(day=1)

        # Set the selected month for use in the context
        self.selected_month = selected_month

        # Filter investments by the selected month
        start_date = selected_month
        end_date = (selected_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        return Investment.objects.filter(user=self.request.user, purchase_date__gte=start_date, purchase_date__lte=end_date)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get active and closed investments for the selected month
        active_investments = self.get_queryset().filter(status='ACTIVE')
        closed_investments = self.get_queryset().filter(status='CLOSED')

        # Calculate Total Invested, Current Value, and Profit/Loss
        total_invested = active_investments.aggregate(total=Sum('amount'))['total'] or 0
        total_value = sum(inv.current_price * inv.units for inv in active_investments)
        total_profit_loss = total_value - total_invested

        # Group investments by type
        investment_types = {}
        for investment_type in InvestmentType.objects.all():
            type_investments = active_investments.filter(investment_type=investment_type)
            if type_investments.exists():
                investment_types[investment_type.id] = {
                    'name': investment_type.name,
                    'currency': type_investments.first().get_currency_symbol(),
                    'amount': type_investments.aggregate(total=Sum('amount'))['total'] or 0,
                    'current_value': sum(inv.current_price * inv.units for inv in type_investments),
                    'profit_loss': type_investments.aggregate(total=Sum('profit_loss'))['total'] or 0,
                    'count': type_investments.count()
                }

        # Group investments by broker
        brokers = {}
        for broker in Broker.objects.filter(user=self.request.user):
            broker_investments = active_investments.filter(broker=broker)
            if broker_investments.exists():
                brokers[broker.id] = {
                    'name': broker.name,
                    'currency': broker_investments.first().get_currency_symbol(),
                    'amount': broker_investments.aggregate(total=Sum('amount'))['total'] or 0,
                    'current_value': sum(inv.current_price * inv.units for inv in broker_investments),
                    'profit_loss': broker_investments.aggregate(total=Sum('profit_loss'))['total'] or 0,
                    'count': broker_investments.count()
                }

        # Calculate total invested by currency
        total_invested_by_currency = {}
        for investment in active_investments:
            currency = investment.currency
            if currency not in total_invested_by_currency:
                total_invested_by_currency[currency] = 0
            total_invested_by_currency[currency] += investment.amount

        # Calculate total invested, total value, and profit/loss by currency
        total_value_by_currency = {}
        profit_loss_by_currency = {}
        for investment in active_investments:
            currency = investment.currency
            if currency not in total_value_by_currency:
                total_value_by_currency[currency] = 0
                profit_loss_by_currency[currency] = 0

            current_value = investment.current_price * investment.units
            total_value_by_currency[currency] += current_value
            profit_loss_by_currency[currency] += current_value - investment.amount

        # Define currency conversion rates to INR (example rates, replace with actual rates)
        conversion_rates = {
            'INR': 1,
            'USD': 84.58,
            'EUR': 85,
            'GBP': 100
        }

        # Convert total invested, total value, and profit/loss to INR
        total_invested_inr = 0
        total_value_inr = 0
        total_profit_loss_inr = 0

        for investment in active_investments:
            currency = investment.currency
            conversion_rate = Decimal(conversion_rates.get(currency, 1))

            total_invested_inr += investment.amount * conversion_rate
            current_value = investment.current_price * investment.units
            total_value_inr += current_value * conversion_rate
            total_profit_loss_inr += (current_value - investment.amount) * conversion_rate

        # Calculate previous and next months for navigation
        prev_month = self.selected_month - timedelta(days=1)
        prev_month = prev_month.replace(day=1)
        next_month = (self.selected_month.replace(day=28) + timedelta(days=4)).replace(day=1)

        context.update({
            'active_investments': active_investments,
            'closed_investments': closed_investments,
            'total_invested': total_invested_inr,
            'total_value': total_value_inr,
            'total_profit_loss': total_profit_loss_inr,
            'investment_types': investment_types,
            'brokers': brokers,
            'total_invested_by_currency': total_invested_by_currency,
            'total_value_by_currency': total_value_by_currency,
            'profit_loss_by_currency': profit_loss_by_currency,
            'current_month_name': self.selected_month.strftime('%B %Y'),
            'prev_month': prev_month,
            'next_month': next_month,
        })

        return context


class InvestmentCreateView(LoginRequiredMixin, CreateView):
    model = Investment
    template_name = 'investment_app/investment_form.html'
    form_class = InvestmentForm
    success_url = reverse_lazy('investment_app:investment_list')

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


class InvestmentCloneView(LoginRequiredMixin, CreateView):
    model = Investment
    template_name = 'investment_app/investment_form.html'
    form_class = InvestmentForm
    success_url = reverse_lazy('investment_app:investment_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Get the original investment to clone
        original_id = self.kwargs.get('pk')
        if original_id:
            original = Investment.objects.filter(pk=original_id, user=self.request.user).first()
            if original and not kwargs.get('instance'):
                # Use original's data but create a new form instance
                kwargs['initial'] = {
                    'broker': original.broker,
                    'investment_type': original.investment_type,
                    'name': original.name,
                    'amount': original.amount,
                    'currency': original.currency,
                    'units': original.units,
                    'purchase_price': original.purchase_price,
                    'current_price': original.current_price,
                    'purchase_date': timezone.now().date(),  # Use current date
                    'transaction_type': original.transaction_type,
                    'status': original.status,
                    'maturity_date': original.maturity_date,
                    'notes': original.notes
                }
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['investment_types'] = InvestmentType.objects.all()
        context['clone_mode'] = True
        context['original_id'] = self.kwargs.get('pk')
        return context


class InvestmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Investment
    template_name = 'investment_app/investment_form.html'
    form_class = InvestmentForm
    success_url = reverse_lazy('investment_app:investment_list')

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
    template_name = 'investment_app/investment_confirm_delete.html'
    success_url = reverse_lazy('investment_app:investment_list')

    def get_queryset(self):
        return Investment.objects.filter(user=self.request.user)


# Broker Views
class BrokerListView(LoginRequiredMixin, ListView):
    model = Broker
    template_name = 'investment_app/broker_list.html'
    context_object_name = 'brokers'

    def get_queryset(self):
        return Broker.objects.filter(user=self.request.user).order_by('name')


class BrokerCreateView(LoginRequiredMixin, CreateView):
    model = Broker
    form_class = BrokerForm
    template_name = 'investment_app/broker_form.html'
    success_url = reverse_lazy('investment_app:broker_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class BrokerUpdateView(LoginRequiredMixin, UpdateView):
    model = Broker
    form_class = BrokerForm
    template_name = 'investment_app/broker_form.html'
    success_url = reverse_lazy('investment_app:broker_list')

    def get_queryset(self):
        return Broker.objects.filter(user=self.request.user)


class BrokerDeleteView(LoginRequiredMixin, DeleteView):
    model = Broker
    template_name = 'investment_app/broker_confirm_delete.html'
    success_url = reverse_lazy('investment_app:broker_list')

    def get_queryset(self):
        return Broker.objects.filter(user=self.request.user)


# Investment Type Views
class InvestmentTypeListView(LoginRequiredMixin, ListView):
    model = InvestmentType
    template_name = 'investment_app/investment_type_list.html'
    context_object_name = 'investment_types'

    def get_queryset(self):
        return InvestmentType.objects.all().order_by('name')


class InvestmentTypeCreateView(LoginRequiredMixin, CreateView):
    model = InvestmentType
    form_class = InvestmentTypeForm
    template_name = 'investment_app/investment_type_form.html'
    success_url = reverse_lazy('investment_app:investment_type_list')


class InvestmentTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = InvestmentType
    form_class = InvestmentTypeForm
    template_name = 'investment_app/investment_type_form.html'
    success_url = reverse_lazy('investment_app:investment_type_list')


class InvestmentTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = InvestmentType
    template_name = 'investment_app/investment_type_confirm_delete.html'
    success_url = reverse_lazy('investment_app:investment_type_list')
