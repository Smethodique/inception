FROM alpine:3.22.1
RUN apk --no-cache add nginx nginx-mod-stream gettext

ENV DOMAIN_NAME=stakhtou.42.fr

COPY config/nginx.conf.template /etc/nginx/nginx.conf.template

COPY certs/stakhtou.42.fr.crt /etc/ssl/certs/stakhtou.42.fr.crt
COPY certs/stakhtou.42.fr.key /etc/ssl/private/stakhtou.42.fr.key
RUN chmod 600 /etc/ssl/private/stakhtou.42.fr.key

RUN mkdir -p /run/nginx /var/log/nginx /var/www/html

EXPOSE 80 443

CMD ["sh", "-c", "envsubst '$$DOMAIN_NAME' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"]
