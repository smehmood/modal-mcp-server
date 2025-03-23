FROM python:3.11-slim

WORKDIR /app

# Install uv for faster Python package installation
RUN pip install --no-cache-dir uv

# Copy project configuration
COPY pyproject.toml .

# Install dependencies using uv
RUN uv pip install --no-cache .

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Start the application
CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8000"] 