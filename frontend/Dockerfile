FROM node:20-alpine

# Install system dependencies
RUN apk add --no-cache \
    wget \
    nginx \
    ca-certificates \
    iputils \
    curl \
    bash

# Create user 'user' with home directory /home/user
RUN adduser -D -h /home/user user

# Create necessary directories and set permissions for nginx
RUN mkdir -p /tmp/nginx /var/cache/nginx /var/log/nginx /usr/share/nginx/html \
    && touch /tmp/nginx.pid \
    && chown -R user:user /tmp/nginx /var/cache/nginx /var/log/nginx /tmp/nginx.pid /usr/share/nginx/html \
    && chmod -R 755 /tmp/nginx /var/cache/nginx /var/log/nginx /tmp/nginx.pid /usr/share/nginx/html

# Set working directory
WORKDIR /home/user/app

# Copy Node.js dependencies files
COPY --chown=user:user package*.json ./

# Install Node.js dependencies
RUN npm ci

# Copy application source code
COPY --chown=user:user . ./

# Set permissions
RUN chown -R user:user /home/user \
    && chmod -R 755 /home/user

# Set environment variables
ARG NODE_ENV=development
ENV NODE_ENV=$NODE_ENV \
    NODE_LOG_LEVEL=${NODE_ENV:-development} \
    VITE_API_BASE_URL=http://localhost:8080

# Build production assets if in production mode
RUN if [ "$NODE_ENV" = "production" ]; then \
    npm run build && \
    cp -r /home/user/app/dist/* /usr/share/nginx/html/ \
    ; fi

# Switch to non-root user
USER user

# Expose port
EXPOSE 3000

# Set entrypoint
ENTRYPOINT ["sh", "./entrypoint"]
