FROM alpine:3.22.1

# Install nginx and create necessary directories
RUN apk add --no-cache nginx && \
    mkdir -p /usr/share/nginx/html && \
    mkdir -p /run/nginx && \
    mkdir -p /var/log/nginx

# Copy the portfolio HTML file
COPY portfolio.html /usr/share/nginx/html/index.html

# Copy nginx configuration for static files
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]