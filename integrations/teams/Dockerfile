FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY teams_app.py .

# Expose port
EXPOSE 3001

# Run the application
CMD ["uvicorn", "teams_app:app", "--host", "0.0.0.0", "--port", "3001"]