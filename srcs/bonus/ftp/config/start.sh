#!/bin/bash

set -e

: "${FTP_USER:=ftpuser}" 
: "${FTP_PASS:=ftppassword}" 
: "${PASV_ADDRESS:=auto}"

if ! id -u "$FTP_USER" >/dev/null 2>&1; then
    adduser -D -h /var/www/html -s /bin/bash "$FTP_USER"
    echo "$FTP_USER:$FTP_PASS" | chpasswd
fi

echo "$FTP_USER" > /etc/vsftpd/user_list

mkdir -p /var/empty /var/log/vsftpd /var/www/html
chown -R "$FTP_USER":"$FTP_USER" /var/www/html
chmod -R 755 /var/www/html


if [ -z "$PASV_ADDRESS" ] || [ "$PASV_ADDRESS" = "auto" ]; then
    PASV_ADDRESS=$(ip route get 1.1.1.1 | awk '{for(i=1;i<=NF;i++){if($i=="src"){print $(i+1);exit}}}')
    
    if [ -z "$PASV_ADDRESS" ] || [ "$PASV_ADDRESS" = "0.0.0.0" ]; then
        PASV_ADDRESS="127.0.0.1"
    fi
    
    echo "Auto-detected PASV_ADDRESS: $PASV_ADDRESS"
fi

sed -i "s/PASV_ADDRESS_PLACEHOLDER/$PASV_ADDRESS/" /etc/vsftpd/vsftpd.conf

echo "Using PASV_ADDRESS=$PASV_ADDRESS"

echo "Starting FTP server..."
exec /usr/sbin/vsftpd /etc/vsftpd/vsftpd.conf