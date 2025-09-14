#!/bin/sh

# Configure PHP-FPM to run properly
sed -i 's/listen = 127.0.0.1:9000/listen = 0.0.0.0:9000/' /etc/php83/php-fpm.d/www.conf
sed -i 's/;clear_env = no/clear_env = no/' /etc/php83/php-fpm.d/www.conf

# Start PHP-FPM in the background
php-fpm83 -F -D

# Start Nginx in the foreground
nginx -g 'daemon off;'