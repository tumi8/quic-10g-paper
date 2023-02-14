# nginx requires version 1.19 for this config to work, debian has 1.18 :(
# from https://joshtronic.com/2018/12/17/how-to-install-the-latest-nginx-on-debian-and-ubuntu/

cat <<EOF >> /etc/apt/sources.list.d/nginx.list
deb http://nginx.org/packages/debian/ bullseye nginx
deb-src http://nginx.org/packages/debian/ bullseye nginx
EOF

curl -L https://nginx.org/keys/nginx_signing.key | apt-key add -

apt update -yqqq
# nginx, envsubst
apt install -y nginx gettext 

# Stop daemon to run in foreground later
systemctl stop nginx

# Rename the nginx binary, so the interop runner can kill it
if [ -f "/usr/sbin/nginx" ]; then
    mv /usr/sbin/nginx /usr/sbin/nginx-server
fi

# Setup certs
if ! [ -d "/etc/nginx/ssl" ]; then
    mkdir /etc/nginx/ssl
    cp -f cert.pem /etc/nginx/ssl/cert.pem 
    cp -f key.pem /etc/nginx/ssl/key.pem 
fi

# remove default, run-server.sh envsubst creates a per-run default site
rm -f /etc/nginx/sites-enabled/default
cp -f nginx.conf /etc/nginx/nginx.conf
