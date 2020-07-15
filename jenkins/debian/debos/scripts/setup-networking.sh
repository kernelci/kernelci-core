#!/bin/bash

set -e

# Network management
systemctl enable systemd-networkd
# DNS resolving
systemctl enable systemd-resolved
# NTP client
systemctl enable systemd-timesyncd

ln -sf /lib/systemd/resolv.conf /etc/resolv.conf

# Setup some static DNS defaults (Google Public)
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
echo "nameserver 8.8.4.4" >> /etc/resolv.conf
