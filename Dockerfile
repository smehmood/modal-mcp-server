FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the Modal CLI
RUN pip install --no-cache-dir modal-client

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Start the application
CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8000"] 