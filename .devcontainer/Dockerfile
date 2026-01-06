FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm

# Install system dependencies for the application
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Set default shell to bash for better experience
SHELL ["/bin/bash", "-c"]

# Create working directory
WORKDIR /workspaces/archive-system

# Default command when container starts
CMD ["/bin/bash", "-c", "echo 'Container started. Run ./scripts/codespaces-start.sh to start the app.'"]
