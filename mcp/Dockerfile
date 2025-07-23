FROM python:3.13-alpine

# Create a working directory
WORKDIR /app

# Install system dependencies
RUN apk update && apk add --no-cache \
    build-base \
    wget \
    nginx \
    ca-certificates \
    iputils \
    curl \
    supervisor \
    bash \
    # Dependencies for shapely
    geos \
    geos-dev \
    # Rust for building tiktoken and other Rust-based Python packages
    rust \
    cargo

# Copy requirements first, install
RUN pip install --no-cache-dir uv

# Create user 'user' with home directory /home/user
RUN adduser -D -h /home/user user

# Set working directory
WORKDIR /home/user/

# Copy Python dependencies files
COPY --chown=user:user pyproject.toml uv.lock ./

# Install Python dependencies using uv
RUN uv sync --frozen

# Copy application source code
COPY app/ /home/user/app
RUN cp -r /home/user/.venv /home/user/app/.venv

# Set permissions
RUN chown -R user:user /home/user \
    && chmod -R 755 /home/user \
    && chown -R user:user /var/log/nginx /var/lib/nginx /tmp

WORKDIR /home/user/app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/user/app:${PATH}"

# Switch to non-root user
USER user

# Expose the port if needed
EXPOSE 8000

# Default environment variables can be set here or in docker-compose
ENV PYTHONUNBUFFERED=1

CMD ["sh", "./entrypoint"]
