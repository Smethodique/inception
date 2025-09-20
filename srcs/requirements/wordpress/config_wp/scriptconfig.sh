#!/bin/sh

if [ ! -f /var/www/html/wp-settings.php ]; then
    echo "WordPress core not found in volume. Downloading..."
    wget -q https://wordpress.org/latest.tar.gz -O /tmp/wordpress.tar.gz && \
    tar -xzf /tmp/wordpress.tar.gz -C /tmp && \
    cp -a /tmp/wordpress/. /var/www/html/ && \
    rm -rf /tmp/wordpress /tmp/wordpress.tar.gz && \
    chown -R www-data:www-data /var/www/html && \
    echo "WordPress core populated."
fi


echo "Waiting for MariaDB to be ready..."
while ! nc -z mariadb 3306; do 
    echo "Waiting for MariaDB..."
    sleep 2
done
echo "MariaDB is ready!"

# Wait for Redis after MariaDB
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
    echo "Waiting for Redis..."
    sleep 2
done
echo "Redis is ready!"

# Create wp-config.php if not exists
if [ ! -f /var/www/html/wp-config.php ]; then
  echo "Creating WordPress configuration..."
  cat > /var/www/html/wp-config.php << EOF
<?php
define('DB_NAME', '${MYSQL_DATABASE}');
define('DB_USER', '${MYSQL_USER}');
define('DB_PASSWORD', '${MYSQL_PASSWORD}');
define('DB_HOST', 'mariadb:3306');
define('DB_CHARSET', 'utf8');

// Redis configuration
define('WP_CACHE', true);
define('WP_REDIS_HOST', '${REDIS_HOST}');
define('WP_REDIS_PORT', ${REDIS_PORT});
define('WP_REDIS_PREFIX', 'wp_post_cache:');
define('WP_REDIS_SELECTIVE_FLUSH', true);
define('WP_REDIS_MAXTTL', 86400);
define('WP_REDIS_CLIENT', 'phpredis');

// Unique Keys and Salts (generated if not provided)
EOF
  wget -qO - https://api.wordpress.org/secret-key/1.1/salt/ >> /var/www/html/wp-config.php
  cat >> /var/www/html/wp-config.php << 'EOF'

$table_prefix = 'wp_';

define('WP_DEBUG', false);

if ( ! defined( 'ABSPATH' ) ) {
    define( 'ABSPATH', __DIR__ . '/' );
}

require_once ABSPATH . 'wp-settings.php';
EOF

  # Set permissions
  chown www-data:www-data /var/www/html/wp-config.php
  chmod 644 /var/www/html/wp-config.php
  echo "wp-config.php created successfully!"
else
  echo "wp-config.php already exists."
fi

# Install WordPress if not already installed
if ! wp core is-installed --path=/var/www/html --allow-root; then
    echo "Installing WordPress..."
    wp core install \
        --path=/var/www/html \
        --url="${DOMAIN_NAME}" \
        --title="${WP_TITLE}" \
        --admin_user="${WP_ADMIN_USER}" \
        --admin_password="${MYSQL_PASSWORD}" \
        --admin_email="${WP_ADMIN_EMAIL}" \
        --skip-email \
        --allow-root

    wp user create "${WP_USER}" "${WP_USER_EMAIL}" \
        --user_pass="${MYSQL_PASSWORD}" \
        --role=author \
        --path=/var/www/html \
        --allow-root
      
    wp plugin install redis-cache --activate --path=/var/www/html --allow-root
    wp redis enable --path=/var/www/html --allow-root


    wp config set WP_REDIS_HOST "${REDIS_HOST}" --path=/var/www/html --allow-root
    wp config set WP_REDIS_PORT "${REDIS_PORT}" --path=/var/www/html --allow-root
    wp config set WP_REDIS_TIMEOUT "${REDIS_TIMEOUT}" --path=/var/www/html --allow-root
    wp config set WP_REDIS_READ_TIMEOUT "${REDIS_READ_TIMEOUT}" --path=/var/www/html --allow-root


    echo "WordPress installation completed!"
else
    echo "WordPress is already installed."
fi

# Install and configure Redis (whether WordPress is newly installed or not)
wp plugin install redis-cache --activate --path=/var/www/html --allow-root || true
wp redis enable --path=/var/www/html --allow-root || true

echo "WordPress and Redis configuration completed!"
