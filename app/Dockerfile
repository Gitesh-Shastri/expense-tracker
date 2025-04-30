# Stage 1 - Build dependencies
FROM python:3.13-alpine AS builder

# Install essential build dependencies
RUN apk add --no-cache \
    build-base \
    libpq-dev

# Install pip without cache
RUN pip install --upgrade pip

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2 - Final lightweight image
FROM python:3.13-alpine AS final

# Install runtime dependencies
RUN apk add --no-cache libpq

# Set environment variables for cleaner logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set a non-root user
ARG USERNAME=expensetracker
RUN adduser -D $USERNAME

# Copy dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.13 /usr/local/lib/python3.13

WORKDIR /dockerapp
COPY . .

# Switch to non-root user
USER $USERNAME

# Expose port if needed (example: 8000 for Django)
EXPOSE 8000
