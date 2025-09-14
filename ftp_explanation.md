# FTP Server Configuration and Theory Explanation

## Table of Contents
1. [FTP Protocol Overview](#ftp-protocol-overview)
2. [vsftpd Configuration](#vsftpd-configuration)
3. [Docker Container Setup](#docker-container-setup)
4. [Security Considerations](#security-considerations)
5. [Troubleshooting](#troubleshooting)
6. [Alternative Protocols](#alternative-protocols)

## FTP Protocol Overview

### What is FTP?
File Transfer Protocol (FTP) is a standard network protocol used for transferring files between a client and server on a computer network. It was one of the earliest protocols developed for the Internet and operates on the application layer of the TCP/IP protocol suite.

### FTP Architecture
FTP uses a **client-server model** with two separate connections:

1. **Control Connection (Port 21)**: Used for sending commands and receiving responses
2. **Data Connection**: Used for actual file transfers

### FTP Modes

#### Active Mode (PORT)
- Client opens a random port and tells server to connect to it
- Server initiates data connection from port 20 to client's port
- **Problem**: Firewalls often block incoming connections to clients

#### Passive Mode (PASV)
- Client requests passive mode
- Server opens a random port and tells client the port number
- Client initiates data connection to server's port
- **Advantage**: Works better with firewalls and NAT

```
Active Mode Flow:
Client:21 ←→ Server:21 (Control)
Client:N  ←── Server:20 (Data)

Passive Mode Flow:
Client:21 ←→ Server:21 (Control)
Client:M  ──→ Server:N (Data)
```

## vsftpd Configuration

### Basic Configuration Options

```conf
# Core Settings
listen=YES                    # Run as standalone daemon
listen_ipv6=NO               # Disable IPv6 support
anonymous_enable=NO          # Disable anonymous access
local_enable=YES             # Enable local user accounts
write_enable=YES             # Allow uploads/modifications
```

### Security Settings

```conf
# Chroot Configuration
chroot_local_user=YES        # Jail users to their home directory
allow_writeable_chroot=YES   # Allow writable chroot (needed for uploads)
secure_chroot_dir=/var/empty # Empty directory for chroot security

# User Management
userlist_enable=YES          # Enable user list
userlist_file=/etc/vsftpd/user_list  # User whitelist file
userlist_deny=NO            # Whitelist mode (only listed users allowed)
```

### Passive Mode Configuration

```conf
# Passive Mode Settings
pasv_enable=YES              # Enable passive mode
pasv_min_port=21000         # Minimum passive port range
pasv_max_port=21010         # Maximum passive port range
pasv_address=domain.com     # Address advertised to clients
```

**Why Passive Ports Matter:**
- Clients need to connect to these ports for data transfers
- Must be accessible through firewalls
- Docker needs to expose these ports

### Container-Specific Settings

```conf
# Container Environment Fixes
seccomp_sandbox=NO          # Disable seccomp (prevents "child died" errors)
session_support=NO          # Disable PAM session support
tcp_wrappers=NO            # Disable TCP wrappers
```

### Logging Configuration

```conf
# Logging Settings
xferlog_enable=YES          # Enable transfer logging
xferlog_file=/var/log/vsftpd/xferlog  # Log file location
log_ftp_protocol=YES        # Log FTP protocol conversations
```

## Docker Container Setup

### Dockerfile Analysis

```dockerfile
FROM alpine:3.22.1

# Install vsftpd and required packages
RUN apk add --no-cache vsftpd openssl bash

# Create required directories
RUN mkdir -p /var/www/html /var/log/vsftpd /etc/vsftpd

# Create FTP user
RUN adduser -D -h /var/www/html -s /bin/bash ftpuser && \
    echo "ftpuser:ftppassword" | chpasswd

# Copy configuration files
COPY config/vsftpd.conf /etc/vsftpd/vsftpd.conf
COPY config/start.sh /start.sh

# Set permissions
RUN chmod +x /start.sh && chown -R ftpuser:ftpuser /var/www/html

# Expose ports
EXPOSE 21 21000-21010

CMD ["/start.sh"]
```

### Start Script Analysis

```bash
#!/bin/bash
set -e

# Environment variables with defaults
: "${FTP_USER:=ftpuser}" 
: "${FTP_PASS:=ftppassword}" 
: "${PASV_ADDRESS:=${DOMAIN_NAME}}"

# Ensure user exists (idempotent)
if ! id -u "$FTP_USER" >/dev/null 2>&1; then
    adduser -D -h /var/www/html -s /bin/bash "$FTP_USER"
    echo "$FTP_USER:$FTP_PASS" | chpasswd
fi

# Configure user list
echo "$FTP_USER" > /etc/vsftpd/user_list

# Create directories and set permissions
mkdir -p /var/empty /var/log/vsftpd /var/www/html
chown -R "$FTP_USER":"$FTP_USER" /var/www/html
chmod -R 755 /var/www/html

# Auto-detect IP if PASV_ADDRESS not set
if [ -z "$PASV_ADDRESS" ] || [ "$PASV_ADDRESS" = "auto" ]; then
    PASV_ADDRESS=$(ip route get 1.1.1.1 | awk 'NR==1 {for(i=1;i<=NF;i++){if($i=="src"){print $(i+1);exit}}}')
fi

# Substitute PASV address in config
sed -i "s/PASV_ADDRESS_PLACEHOLDER/$PASV_ADDRESS/" /etc/vsftpd/vsftpd.conf

echo "Using PASV_ADDRESS=$PASV_ADDRESS"
echo "Starting FTP server..."

# Start vsftpd
exec /usr/sbin/vsftpd /etc/vsftpd/vsftpd.conf
```

### Docker Compose Integration

```yaml
ftp:
  build: bonus/ftp/
  env_file:
    - .env
  volumes:
    - wordpress_data:/var/www/html  # Share WordPress files
  networks:
    - inception_network
  environment:
    - FTP_USER=ftpuser
    - FTP_PASS=ftppassword
    - PASV_ADDRESS=${DOMAIN_NAME}
  ports:
    - "21:21"                    # Control port
    - "21000-21010:21000-21010"  # Passive data ports
```

## Security Considerations

### 1. Plain Text Credentials
**Problem**: FTP sends usernames and passwords in plain text
**Solutions**:
- Use FTPS (FTP over SSL/TLS)
- Consider SFTP (SSH File Transfer Protocol)
- Restrict to trusted networks

### 2. Chroot Jail
**Purpose**: Prevent users from accessing files outside their home directory
**Implementation**:
```conf
chroot_local_user=YES
allow_writeable_chroot=YES
```

### 3. User Restrictions
```conf
userlist_enable=YES          # Enable user filtering
userlist_deny=NO            # Whitelist mode
max_clients=50              # Limit concurrent connections
max_per_ip=5                # Limit connections per IP
```

### 4. Network Security
- Use passive mode to work with firewalls
- Limit passive port range
- Consider VPN for sensitive data

## Troubleshooting

### Common Errors and Solutions

#### 1. "500 OOPS: child died"
**Causes**:
- seccomp sandbox conflicts in containers
- Permission issues
- Invalid configuration

**Solutions**:
```conf
seccomp_sandbox=NO
session_support=NO
tcp_wrappers=NO
```

#### 2. "425 Security: Bad IP connecting"
**Cause**: PASV address mismatch
**Solution**: Set correct `pasv_address`

#### 3. Connection hangs during file listing
**Cause**: Passive mode issues
**Solutions**:
- Enable passive mode in client
- Check firewall rules for passive ports
- Verify PASV address is reachable

#### 4. Permission denied errors
**Causes**:
- Incorrect file ownership
- Wrong directory permissions
- Chroot configuration issues

**Solutions**:
```bash
chown -R ftpuser:ftpuser /var/www/html
chmod -R 755 /var/www/html
```

### Debugging Commands

```bash
# Check container logs
docker logs srcs-ftp-1

# Verify configuration
docker exec -it srcs-ftp-1 cat /etc/vsftpd/vsftpd.conf

# Check file permissions
docker exec -it srcs-ftp-1 ls -la /var/www/html

# Test network connectivity
nc -vz stakhtou.42.fr 21

# Check passive ports
nmap -p 21000-21010 stakhtou.42.fr
```

## Alternative Protocols

### SFTP (SSH File Transfer Protocol)
**Advantages**:
- Encrypted connections
- Single port (22)
- Uses SSH authentication
- Better firewall compatibility

**Example Docker setup**:
```dockerfile
FROM alpine:3.22.1
RUN apk add --no-cache openssh-server
# Configure SSH with chroot
```

### FTPS (FTP over SSL/TLS)
**Advantages**:
- Encrypted FTP
- Compatible with existing FTP clients
- Can use certificates

**vsftpd FTPS config**:
```conf
ssl_enable=YES
rsa_cert_file=/etc/ssl/certs/vsftpd.crt
rsa_private_key_file=/etc/ssl/private/vsftpd.key
force_local_data_ssl=YES
force_local_logins_ssl=YES
```

### Web-based File Managers
**Examples**:
- FileBrowser
- Nextcloud
- ownCloud

**Advantages**:
- No special client needed
- Works through web browsers
- Better user interface
- Integration with web applications

## Best Practices

1. **Use strong authentication**
2. **Enable logging and monitoring**
3. **Regularly update vsftpd**
4. **Limit user access appropriately**
5. **Consider alternatives like SFTP for sensitive data**
6. **Implement proper backup strategies**
7. **Test configurations thoroughly**

## Conclusion

FTP remains useful for file transfers, especially in development environments and legacy systems. However, for production use with sensitive data, consider more secure alternatives like SFTP or HTTPS-based file transfer mechanisms.

The key to successful FTP deployment in containers is understanding the passive mode requirements, proper port mapping, and container-specific configuration adjustments like disabling seccomp sandbox.