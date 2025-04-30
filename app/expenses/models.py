from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Bank(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('SAVINGS', 'Savings Account'),
        ('CURRENT', 'Current Account'),
        ('CREDIT', 'Credit Card'),
        ('LOAN', 'Loan Account'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.account_number} ({self.account_type})"

    class Meta:
        verbose_name_plural = "Banks"
        ordering = ['-updated_at']

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Expense(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, default='DEBIT')
    date = models.DateTimeField()
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.description} - ₹{self.amount} ({self.category})"

    def save(self, *args, **kwargs):
        # If this is a new expense and opening_balance is provided, update the bank balance
        if not self.pk and self.opening_balance is not None:
            self.bank.balance = self.opening_balance
            self.bank.save()
        super().save(*args, **kwargs)

class EMI(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('SKIPPED', 'Skipped'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    due_date_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.description} - {self.amount}"

    def is_due_this_month(self):
        today = timezone.now()
        return (
            self.due_date_time.year == today.year and
            self.due_date_time.month == today.month
        )

    def get_months_remaining(self):
        today = timezone.now().date()
        if today > self.end_date:
            return 0
        return (self.end_date.year - today.year) * 12 + (self.end_date.month - today.month)

    def mark_as_paid(self):
        if self.status == 'PENDING':
            self.status = 'PAID'
            self.save()
            
            # Create an expense record for the paid EMI
            Expense.objects.create(
                user=self.user,
                bank=self.bank,
                amount=self.amount,
                description=f"EMI Payment: {self.description}",
                category=self.category,
                transaction_type='DEBIT',
                date=timezone.now()
            )
            
            # Create a new EMI entry for next month if we haven't reached the end date
    
            # Calculate next month properly using timezone-aware dates
            if self.due_date_time.month == 12:
                next_month = timezone.datetime(
                    year=self.due_date_time.year + 1,
                    month=1,
                    day=min(self.due_date_time.day, 28),  # Avoid invalid dates for February
                    hour=self.due_date_time.hour,
                    minute=self.due_date_time.minute,
                    tzinfo=timezone.get_current_timezone()
                )
            else:
                next_month = timezone.datetime(
                    year=self.due_date_time.year,
                    month=self.due_date_time.month + 1,
                    day=min(self.due_date_time.day, 28),  # Avoid invalid dates
                    hour=self.due_date_time.hour,
                    minute=self.due_date_time.minute,
                    tzinfo=timezone.get_current_timezone()
                )
            
            if next_month.date() <= self.end_date:
                EMI.objects.create(
                    user=self.user,
                    bank=self.bank,
                    amount=self.amount,
                    description=self.description,
                    category=self.category,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    due_date_time=next_month,
                    status='PENDING'
                )

class Broker(models.Model):
    """Investment broker model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.account_number}"

class InvestmentType(models.Model):
    """Investment type model (e.g., Stocks, Mutual Fund, Fixed Deposit)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    risk_level = models.CharField(max_length=20, choices=[
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Investment(models.Model):
    """Investment model"""
    TRANSACTION_TYPE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE)
    investment_type = models.ForeignKey(InvestmentType, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    units = models.DecimalField(max_digits=15, decimal_places=4, default=1.0)
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2)
    current_price = models.DecimalField(max_digits=15, decimal_places=2)
    purchase_date = models.DateField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, default='BUY')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    maturity_date = models.DateField(null=True, blank=True)
    profit_loss = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.investment_type}"

    def save(self, *args, **kwargs):
        # Calculate profit/loss
        if self.units and self.current_price and self.purchase_price:
            if self.transaction_type == 'BUY':
                self.profit_loss = (self.current_price - self.purchase_price) * self.units
            else:  # SELL
                self.profit_loss = (self.purchase_price - self.current_price) * self.units
        super().save(*args, **kwargs)
