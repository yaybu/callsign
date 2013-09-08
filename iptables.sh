sudo iptables -tnat -A OUTPUT -p tcp -d127.0.0.0/8 --dport 53 -j REDIRECT --to-port 5053
sudo iptables -tnat -A OUTPUT -p udp -d127.0.0.0/8 --dport 53 -j REDIRECT --to-port 5053
