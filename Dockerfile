FROM python:3.11-slim

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /workspace/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /workspace/

# Create cache directory
RUN mkdir -p /workspace/.cache/schemas

# Verify installation
RUN python -c "from src.introspection import ApiSchemaIntrospector; print('Phase 1 OK')"
RUN python -c "from src.builder import PayloadBuilder; print('Phase 2 OK')"

# Default command
CMD ["/bin/bash"]
