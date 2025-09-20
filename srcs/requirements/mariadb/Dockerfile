FROM alpine:3.22.1

RUN apk add --no-cache mariadb mariadb-client bash

RUN mkdir -p /var/lib/mysql /run/mysqld

RUN addgroup -S mysql 2>/dev/null || true && \
    adduser -D -u 1000 -G mysql mysql 2>/dev/null || true

RUN chown -R mysql:mysql /var/lib/mysql /run/mysqld

COPY config/maria_db.conf /etc/my.cnf
COPY config/init_db.sh /init_db.sh
RUN chmod +x /init_db.sh

EXPOSE 3306

# Run initialization script
CMD ["/init_db.sh"]
