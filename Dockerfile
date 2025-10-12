# Dockerfile for CareRoute Flight Agent
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY flight_agent/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY flight_agent/ ./flight_agent/

# Create non-root user
RUN useradd --create-home --shell /bin/bash flightagent
RUN chown -R flightagent:flightagent /app
USER flightagent

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Default environment variables
ENV PROVIDER=flightaware
ENV A2A_PORT=8001
ENV FA_TIMEOUT_SEC=6
ENV GROQ_MODEL=llama-3.1-8b-instant
ENV GROQ_TIMEOUT_SEC=10

# Run the application
CMD ["python", "-m", "flight_agent.simple_a2a_server"]
