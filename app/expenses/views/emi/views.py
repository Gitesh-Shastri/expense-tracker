from django.utils import timezone
from django.db.models import Sum
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from expenses.models import EMI, Category, Bank
from datetime import datetime, timedelta


class EMIListView(LoginRequiredMixin, ListView):
    model = EMI
    template_name = 'expenses/emi/emi_list.html'  # Updated template path
    context_object_name = 'emis'

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

        return EMI.objects.filter(user=self.request.user).order_by('due_date_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add month information for navigation with timezone-aware objects
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
            'today': timezone.localtime(timezone.now()),  # Use timezone-aware current time
        })
        
        return context


class EMICreateView(LoginRequiredMixin, CreateView):
    model = EMI
    template_name = 'expenses/emi/emi_form.html'  # Updated template path
    fields = ['bank', 'amount', 'description', 'category', 'start_date', 'end_date', 'due_date_time']
    success_url = reverse_lazy('emis:emi_list')  # Updated namespace

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
    template_name = 'expenses/emi/emi_form.html'  # Updated template path
    fields = ['bank', 'amount', 'description', 'category', 'start_date', 'end_date', 'due_date_time', 'status']
    success_url = reverse_lazy('emis:emi_list')  # Updated namespace

    def get_queryset(self):
        return EMI.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banks'] = Bank.objects.filter(user=self.request.user)
        context['categories'] = Category.objects.all()
        return context


class EMIDeleteView(LoginRequiredMixin, DeleteView):
    model = EMI
    template_name = 'expenses/emi/emi_confirm_delete.html'  # Updated template path
    success_url = reverse_lazy('emis:emi_list')  # Updated namespace

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