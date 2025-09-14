# WordPress and MariaDB Setup Explanation

## Overview
This document explains the configuration and connection between the WordPress and MariaDB containers in your Docker setup. The architecture follows a secure pattern where only Nginx is exposed to the internet, while WordPress and MariaDB communicate internally.

## Architecture

```
[Internet] ←→ [Nginx:80/443] ←→ [WordPress:9000] ←→ [MariaDB:3306]
```

## 1. Docker Compose Configuration (`docker-compose.yml`)

### Services:

#### Nginx Service
- **Ports**: Exposes ports 80 (HTTP) and 443 (HTTPS) to the host
- **Volumes**: Mounts `wordpress_data` to `/var/www/html`
- **Network**: Connects to `inception_network`
- **Dependencies**: Depends on WordPress service

#### WordPress Service
- **Build**: Uses the Dockerfile in `requirements/wordpress/`
- **Environment**: Loads variables from `.env` file
- **Volumes**: Shares `wordpress_data` volume with Nginx
- **Network**: Connects to `inception_network`
- **Secrets**: Uses `db_password` for database authentication

#### MariaDB Service
- **Build**: Uses the Dockerfile in `requirements/mariadb/`
- **Volumes**: Uses `db_data` volume for persistent storage
- **Network**: Connects to `inception_network`
- **Secrets**: Uses both `db_password` and `db_root_password`

## 2. WordPress Configuration

### Dockerfile

```dockerfile
# Base image
FROM alpine:3.22.1

# Install minimal required PHP extensions
RUN apk add --no-cache \
    php83 php83-fpm php83-mysqli php83-pdo php83-pdo_mysql \
    php83-json php83-curl php83-dom php83-mbstring \
    php83-openssl php83-xml php83-zip php83-phar \
    wget tar bash netcat-openbsd

# Create www-data user and required directories
RUN adduser -u 82 -D -S -G www-data www-data && \
    mkdir -p /var/www/html /run/php

# Configure PHP-FPM
RUN sed -i 's/listen = 127.0.0.1:9000/listen = 0.0.0.0:9000/' /etc/php83/php-fpm.d/www.conf && \
    sed -i 's/;clear_env = no/clear_env = no/' /etc/php83/php-fpm.d/www.conf

# Download and extract WordPress
ARG WP_VERSION=6.8.2
RUN wget -q https://wordpress.org/wordpress-${WP_VERSION}.tar.gz && \
    tar -xzf wordpress-${WP_VERSION}.tar.gz && \
    cp -r wordpress/* /var/www/html/ && \
    rm -rf wordpress wordpress-${WP_VERSION}.tar.gz && \
    chown -R www-data:www-data /var/www/html
```

### Configuration Script (`scriptconfig.sh`)

```bash
#!/bin/bash
set -e

# Wait for MariaDB to be ready
while ! nc -z mariadb 3306; do sleep 2; done

# Read database password from Docker secret
MYSQL_PASSWORD=$(cat /run/secrets/db_password)

# Create minimal wp-config.php
cat > /var/www/html/wp-config.php << EOF
<?php
define('DB_NAME', '${MYSQL_DATABASE}');
define('DB_USER', '${MYSQL_USER}');
define('DB_PASSWORD', '${MYSQL_PASSWORD}');
define('DB_HOST', 'mariadb:3306');
define('DB_CHARSET', 'utf8mb4');
define('DB_COLLATE', '');

\$table_prefix = 'wp_';

define('WP_DEBUG', false);
define('WP_AUTO_UPDATE_CORE', false);

define('ABSPATH', dirname(__FILE__) . '/');
require_once(ABSPATH . 'wp-settings.php');
EOF

# Set secure permissions
chown www-data:www-data /var/www/html/wp-config.php
chmod 600 /var/www/html/wp-config.php

# Install WordPress if not already installed
if ! wp core is-installed --path=/var/www/html --allow-root; then
    wp core install \
        --path=/var/www/html \
        --url="${DOMAIN_NAME}" \
        --title="${WP_TITLE}" \
        --admin_user="${WP_ADMIN_USER}" \
        --admin_password="${MYSQL_PASSWORD}" \
        --admin_email="${WP_ADMIN_EMAIL}" \
        --skip-email \
        --allow-root

    # Create author user
    wp user create "${WP_AUTHOR_USER}" "${WP_AUTHOR_EMAIL}" \
        --user_pass="${MYSQL_PASSWORD}" \
        --role=author \
        --path=/var/www/html \
        --allow-root

    echo "WordPress installation completed!"
fi

echo "WordPress configuration created successfully!"
```

## 3. MariaDB Configuration

### Dockerfile

```dockerfile
# Start with Alpine Linux, a lightweight base image (only ~5MB)
FROM alpine:3.22.1

# Install MariaDB server, client, and bash shell
# --no-cache: Don't store the index locally, reduces image size
RUN apk add --no-cache mariadb mariadb-client bash

# Create necessary directories for MariaDB
# - /var/lib/mysql: Stores all database files
# - /run/mysqld: For the MySQL daemon socket and PID file
# - /var/log/mysql: For database logs
RUN mkdir -p /var/lib/mysql /run/mysqld /var/log/mysql

# Create a non-root 'mysql' user with UID 1000 and add to 'mysql' group
# -D: Don't assign a password (passwordless login)
# -u 1000: Set user ID to 1000
# -G mysql: Add to 'mysql' group
# The || echo part prevents build failure if user exists
RUN adduser -D -u 1000 -G mysql mysql || echo "User mysql already exists"

# Set ownership of database directories to mysql user and group
# -R: Recursively change ownership of directories and contents
RUN chown -R mysql:mysql /var/lib/mysql /run/mysqld /var/log/mysql

# Copy configuration files into the container
# maria_db.conf: Main MariaDB configuration
# init_db.sh: Script to initialize the database
COPY config/maria_db.conf /etc/my.cnf
COPY config/init_db.sh /init_db.sh

# Make the initialization script executable
RUN chmod +x /init_db.sh

# Inform Docker that the container listens on port 3306
# Note: This is just documentation, doesn't actually publish the port
EXPOSE 3306

# Set the command to run when the container starts
# Uses JSON array syntax to avoid shell processing
CMD ["/init_db.sh"]
```

### MariaDB Configuration (`maria_db.conf`)

```ini
[mysqld]
# Basic settings
user = mysql                    # Run the MySQL server as 'mysql' user for security
port = 3306                    # Default MySQL/MariaDB port
# Location where all database files are stored
# This is where tables, indexes, and other database objects are physically stored
datadir = /var/lib/mysql
# Socket file for local connections (faster than TCP/IP)
socket = /run/mysqld/mysqld.sock

# Network configuration
# Listen on all network interfaces (0.0.0.0 means all IPv4 addresses)
# This is necessary for container-to-container communication in Docker
bind-address = 0.0.0.0

# Character set configuration
# utf8mb4 supports full Unicode including emojis and special characters
character-set-server = utf8mb4
# Default collation for comparing and sorting strings
collation-server = utf8mb4_unicode_ci

# Storage engine settings
# InnoDB is the default and most widely used storage engine
# It supports transactions, row-level locking, and foreign keys
default-storage-engine = innodb
# Store each InnoDB table in a separate .ibd file
# This improves performance and makes it easier to recover individual tables
innodb_file_per_table = 1

# Security settings
# Skip hostname resolution for client connections
# This improves performance and prevents potential DNS resolution issues
skip-name-resolve

# Performance settings
# Maximum number of simultaneous client connections
# Lower than default (150) to prevent resource exhaustion in container
max_connections = 50

# Client configuration section
# Applies to all client connections
[client]
# Default character set for client connections
default-character-set = utf8mb4
```

### Initialization Script (`init_db.sh`)

```bash
#!/bin/bash
# Exit immediately if any command fails
set -e

# Security: Read database credentials from Docker secrets
# These are mounted at runtime from the Docker secrets
MYSQL_PASSWORD=$(cat /run/secrets/db_password)
MYSQL_ROOT_PASSWORD=$(cat /run/secrets/db_root_password)

# Check if this is the first run by looking for the mysql system database
if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "Initializing MariaDB for the first time..."
    
    # Initialize the MySQL data directory and create system tables
    # --user: Run as mysql user for security
    # --datadir: Directory where database files are stored
    # --basedir: Base directory where MySQL is installed
    mysql_install_db --user=mysql --datadir=/var/lib/mysql --basedir=/usr
    
    echo "Starting temporary MariaDB instance for initial setup..."
    # Start MariaDB in safe mode (runs in background)
    # --user: Run as mysql user
    # --datadir: Directory containing database files
    mysqld_safe --user=mysql --datadir=/var/lib/mysql &
    
    # Store the process ID to shut it down later
    MYSQL_PID=$!
    
    echo "Waiting for MariaDB to start..."
    # Wait for the server to be ready to accept connections
    # --silent: Don't print connection warnings
    while ! mysqladmin ping --silent; do 
        echo "Still waiting for MariaDB to start..."
        sleep 2 
    done
    
    echo "Configuring initial database and users..."
    # Execute SQL commands to set up the initial database and users
    # The EOF (End Of File) marker starts a here-document
    mysql -u root <<EOF
-- Set root password for localhost access
-- This is the most privileged account
ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD}';

-- Create the application database if it doesn't exist
-- Uses the environment variable set in docker-compose.yml
CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE};

-- Create application user with password from secrets
-- The '%' wildcard allows connection from any host
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD}';

-- Grant all privileges on the application database to the application user
-- This allows the app to create tables, insert data, etc.
GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'%';

-- Make sure all privilege changes take effect immediately
FLUSH PRIVILEGES;
EOF
    
    echo "Shutting down temporary MariaDB instance..."
    # Stop the temporary MySQL instance
    kill $MYSQL_PID
    # Wait for the process to fully terminate
    wait $MYSQL_PID
    
    echo "MariaDB initialization complete!"
fi

echo "Starting MariaDB server..."
# Start MariaDB in the foreground (replaces the current process)
# This is the main process that will keep the container running
exec mysqld --user=mysql --datadir=/var/lib/mysql
```

## 4. Connection Flow

1. **User Access**:
   - User accesses the site via web browser (port 80/443)
   - Nginx receives the request

2. **Nginx to WordPress**:
   - Nginx forwards PHP requests to WordPress container on port 9000 (PHP-FPM)
   - Static files are served directly by Nginx from the shared volume

3. **WordPress to MariaDB**:
   - WordPress connects to MariaDB using the service name `mariadb` on port 3306
   - Authentication uses the credentials from environment variables/secrets
   - The connection is internal to the Docker network

4. **Data Persistence**:
   - WordPress files are stored in the `wordpress_data` volume (shared with Nginx)
   - Database files are stored in the `db_data` volume

## 5. Security Considerations

1. **Network Security**:
   - Only Nginx is exposed to the internet
   - WordPress and MariaDB communicate over an internal Docker network
   - MariaDB is not accessible from outside the Docker network

2. **Authentication**:
   - Database passwords are stored in Docker secrets
   - Root access is restricted to localhost
   - Application uses a dedicated database user with limited privileges

3. **File Permissions**:
   - WordPress files are owned by www-data
   - wp-config.php has restricted permissions (600)
   - Database files are owned by the mysql user

## 6. Environment Variables

Required environment variables (typically in `.env` file):

```
# WordPress
WP_TITLE=My WordPress Site
DOMAIN_NAME=example.com
WP_ADMIN_USER=admin
WP_ADMIN_EMAIL=admin@example.com
WP_AUTHOR_USER=author
WP_AUTHOR_EMAIL=author@example.com

# Database
MYSQL_DATABASE=wordpress
MYSQL_USER=wordpress
# MYSQL_PASSWORD and MYSQL_ROOT_PASSWORD are in secrets
```

## 7. Secrets Management

Secrets are stored in files outside the repository:
- `../secrets/db_password.txt`: Regular database user password
- `../secrets/db_root_password.txt`: Database root password

These files should be kept secure and not committed to version control.
