# Import views from specialized modules
from .expense.views import (
    MonthlyExpenseView,
    ExpenseCreateView,
    ExpenseUpdateView,
    ExpenseDeleteView,
)

from .emi.views import (
    EMIListView,
    EMICreateView,
    EMIUpdateView,
    EMIDeleteView,
    mark_emi_as_paid,
)

from .investment.views import (
    # Investment views
    InvestmentListView,
    InvestmentCreateView,
    InvestmentUpdateView,
    InvestmentDeleteView,
    # Broker views
    BrokerListView,
    BrokerCreateView,
    BrokerUpdateView,
    BrokerDeleteView,
    # Investment Type views
    InvestmentTypeListView,
    InvestmentTypeCreateView,
    InvestmentTypeUpdateView,
    InvestmentTypeDeleteView
)

# Import the home view
from .home import home