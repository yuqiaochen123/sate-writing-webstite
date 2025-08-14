FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8080

# Set environment variable
ENV PORT=8080

# Start the application
CMD ["sh", "-c", "cd backend && gunicorn app:app --bind 0.0.0.0:$PORT"]
