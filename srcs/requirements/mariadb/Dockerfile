FROM alpine:3.22.1

RUN apk add --no-cache mariadb mariadb-client bash

# Create required directories
RUN mkdir -p /var/lib/mysql /run/mysqld

# Create mysql user if it doesn't exist
RUN addgroup -S mysql 2>/dev/null || true && \
    adduser -D -u 1000 -G mysql mysql 2>/dev/null || true

# Set permissions
RUN chown -R mysql:mysql /var/lib/mysql /run/mysqld

# Copy configuration and initialization script
COPY config/maria_db.conf /etc/my.cnf
COPY config/init_db.sh /init_db.sh
RUN chmod +x /init_db.sh

# Expose port
EXPOSE 3306

# Run initialization script
CMD ["/init_db.sh"]
