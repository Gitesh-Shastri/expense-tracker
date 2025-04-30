# Expense Tracker

A full-featured expense tracking application built with Django that helps you manage your personal finances, track expenses, manage EMIs, and monitor investments.

## Features

### Expense Management
- Track daily expenses and income
- Categorize transactions
- Monthly expense view with category breakdown
- Bank account management with balance tracking

### EMI Management
- Track and manage loan EMIs
- Automatically create recurring EMI entries
- Mark EMIs as paid with single-click functionality

### Investment Portfolio
- Track different types of investments (stocks, mutual funds, etc.)
- Monitor investment performance with profit/loss tracking
- Organize investments by broker and type
- Risk level categorization

## Tech Stack

- **Backend**: Django 5.1.7
- **Frontend**: Bootstrap 5.3.0, Font Awesome 6.0.0
- **Database**: PostgreSQL 13
- **Containerization**: Docker & Docker Compose

## Prerequisites

- Docker and Docker Compose
- Git

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/expense_tracker.git
   cd expense_tracker
   ```

2. Create a `.env` file in the project root with the following environment variables:
   ```
   DJANGO_SECRET_KEY=your_secret_key_here
   DJANGO_DEBUG=True
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
   POSTGRES_DB=expensetracker
   POSTGRES_USER=expensetracker
   POSTGRES_PASSWORD=your_secure_password
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   ```

3. Build and start the Docker containers:
   ```
   docker-compose up -d
   ```

4. Create a Django superuser to access the admin interface:
   ```
   docker-compose exec web python manage.py createsuperuser
   ```

5. Apply migrations:
   ```
   docker-compose exec web python manage.py migrate
   ```

## Usage

1. Access the application at `http://localhost:8000`
2. Log in with your superuser credentials
3. Navigate to the admin interface at `http://localhost:8000/admin/` to set up:
   - Categories
   - Bank accounts
   - Investment types

4. Use the main application to:
   - Track monthly expenses at `/expenses/`
   - Manage EMIs at `/expenses/emi/`
   - Manage investments at `/expenses/investments/`

## Project Structure

The main application is organized as follows:

```
app/
├── expenses/            # Main app for expense tracking
│   ├── models.py        # Data models
│   ├── views.py         # View controllers
│   ├── forms.py         # Form definitions
│   ├── urls.py          # URL routing
│   └── templates/       # HTML templates
└── expensetracker/      # Project settings
    ├── settings.py      # Django settings
    └── urls.py          # Main URL routing
```

## Key Models

- **Bank**: Bank account information
- **Category**: Expense categories
- **Expense**: Individual expense/income transactions
- **EMI**: Loan EMI tracking
- **Broker**: Investment brokers
- **InvestmentType**: Types of investments
- **Investment**: Individual investment tracking

## Development

To run the development server with live code changes:

```
docker-compose up
```

Changes will be reflected automatically thanks to the mounted volumes in the Docker configuration.

## License

This project is open source and available under the [MIT License](LICENSE).