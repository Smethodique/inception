#!/bin/bash

set -euo pipefail


# Ensure ownership
chown -R mysql:mysql /var/lib/mysql /run/mysqld

mariadb-install-db --user=mysql --datadir=/var/lib/mysql --auth-root-authentication-method=normal >/dev/null


# Start server (foreground) in background subshell so we can configure
mysqld_safe --datadir='/var/lib/mysql' --port=3306 --user=mysql &
until mysqladmin ping -uroot --silent; do
  sleep 1
done

# Secure and create database / user only first time (wordpress db absent)
if ! mysql -uroot -e "USE ${MYSQL_DATABASE}" >/dev/null 2>&1; then
  echo "[MariaDB] Setting root password and creating database/user..."
  mysql -uroot <<-EOSQL
    ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD}';
    CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD}';
    GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_USER}'@'%';
    FLUSH PRIVILEGES;
EOSQL
else
  exit 0
fi
while ping -c 1 localhost >/dev/null 2>&1; do
  sleep 2
done