FROM alpine:3.22.1

# Install minimal required packages
RUN apk add --no-cache \
    php83 \
    php83-fpm \
    php83-mysqli \
    php83-pdo \
    php83-pdo_mysql \
    php83-json \
    php83-curl \
    php83-dom \
    php83-exif \
    php83-fileinfo \
    php83-mbstring \
    php83-openssl \
    php83-xml \
    php83-zip \
    php83-redis \
    php83-phar \
    php83-intl \
    php83-bcmath \
    php83-ctype \
    php83-session \
    php83-tokenizer \
    php83-simplexml \
    php83-xmlwriter \
    php83-gd \
    wget \
    tar \
    bash \
    netcat-openbsd

# Create www-data user and required directories
RUN adduser -u 82 -D -S -G www-data www-data && \
    mkdir -p /var/www/html /run/php

# Configure PHP-FPM
RUN sed -i 's/listen = 127.0.0.1:9000/listen = 0.0.0.0:9000/' /etc/php83/php-fpm.d/www.conf && \
    sed -i 's/;clear_env = no/clear_env = no/' /etc/php83/php-fpm.d/www.conf

# Create WordPress directory with correct permissions
RUN chown -R www-data:www-data /var/www/html

# Download and extract WordPress
ARG WP_VERSION=6.8.2
RUN wget -q https://wordpress.org/wordpress-${WP_VERSION}.tar.gz && \
    tar -xzf wordpress-${WP_VERSION}.tar.gz && \
    cp -r wordpress/* /var/www/html/ && \
    rm -rf wordpress wordpress-${WP_VERSION}.tar.gz && \
    chown -R www-data:www-data /var/www/html && \
    find /var/www/html -type d -exec chmod 755 {} \; && \
    find /var/www/html -type f -exec chmod 644 {} \; && \
    chmod -R 775 /var/www/html/wp-content && \
    echo "WordPress installation completed."

# Download WP-CLI using the official installation method
RUN wget -O wp-cli.phar https://github.com/wp-cli/wp-cli/releases/download/v2.8.1/wp-cli-2.8.1.phar && \
    chmod +x wp-cli.phar && \
    mv wp-cli.phar /usr/local/bin/wp && \
    wp --info || echo "WP-CLI installed successfully"

COPY config_wp/scriptconfig.sh /scriptconfig.sh
RUN chmod +x /scriptconfig.sh

EXPOSE 9000

# Health check to ensure PHP-FPM is running
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD pgrep php-fpm83 >/dev/null || exit 1

# Run the configuration script and start PHP-FPM
CMD ["/bin/sh", "-c", "chown -R www-data:www-data /var/www/html && /scriptconfig.sh && php-fpm83 -F"]
