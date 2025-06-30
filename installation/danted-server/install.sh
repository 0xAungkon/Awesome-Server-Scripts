apt-get update
apt install dante-server -y
sudo useradd -M -s /usr/sbin/nologin proxyuser
sudo passwd proxyuser
mv /etc/danted.conf /etc/danted.conf.bak
curl -s 'https://raw.githubusercontent.com/0xAungkon/Awesome-Server-Scripts/refs/heads/main/installation/danted-server/etc/danted.conf' > /etc/danted.conf
sudo systemctl enable danted
sudo systemctl restart danted

