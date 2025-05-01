from django.db.models import Sum
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from expenses.models import Investment, InvestmentType, Broker
from .forms import InvestmentForm, BrokerForm, InvestmentTypeForm


class InvestmentListView(LoginRequiredMixin, ListView):
    model = Investment
    template_name = 'investment_app/investment_list.html'
    context_object_name = 'investments'

    def get_queryset(self):
        return Investment.objects.filter(user=self.request.user).order_by('-purchase_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active investments
        active_investments = self.get_queryset().filter(status='ACTIVE')
        
        # Dictionary to store totals by currency
        total_invested_by_currency = {}
        total_value_by_currency = {}
        profit_loss_by_currency = {}
        
        # Calculate investment summary with currency separation
        total_invested = 0
        total_value = 0
        total_profit_loss = 0
        
        for investment in active_investments:
            # Sum values by currency
            currency = investment.currency
            
            # Calculate the current value of this investment
            current_value = investment.current_price * investment.units
            
            # Update currency-specific dictionaries
            if currency not in total_invested_by_currency:
                total_invested_by_currency[currency] = 0
                total_value_by_currency[currency] = 0
                profit_loss_by_currency[currency] = 0
                
            total_invested_by_currency[currency] += investment.amount
            total_value_by_currency[currency] += current_value
            profit_loss_by_currency[currency] += investment.profit_loss
            
            # Also track totals for backwards compatibility
            total_invested += investment.amount
            total_value += current_value
            total_profit_loss += investment.profit_loss
        
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
            'brokers': brokers,
            # Add currency-specific data
            'total_invested_by_currency': total_invested_by_currency,
            'total_value_by_currency': total_value_by_currency,
            'profit_loss_by_currency': profit_loss_by_currency
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
