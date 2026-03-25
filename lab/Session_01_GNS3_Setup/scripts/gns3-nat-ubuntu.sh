#!/usr/bin/env bash
# gns3-nat-ubuntu.sh — NAT setup for GNS3 lab (Ubuntu)
#
# Run this script before opening GNS3 after every reboot.
# On first run it also makes libvirtd and iptables rules persistent.
#
# Usage: sudo ./gns3-nat-ubuntu.sh

set -euo pipefail

# --- detect internet-facing interface ---
IFACE=$(ip route | awk '/^default/ {print $5; exit}')
if [[ -z "$IFACE" ]]; then
    echo "ERROR: could not detect default network interface" >&2
    exit 1
fi
echo "Using interface: $IFACE"

# --- services ---
systemctl enable --now libvirtd.service
systemctl enable --now virtlogd.service

# --- virtual bridge ---
virsh net-autostart default
virsh net-start default 2>/dev/null || true   # "already active" is fine

# --- IP forwarding ---
sysctl -w net.ipv4.ip_forward=1
grep -qxF 'net.ipv4.ip_forward=1' /etc/sysctl.conf \
    || echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf

# --- iptables NAT rules (idempotent) ---
iptables -t nat -C POSTROUTING -o "$IFACE" -j MASQUERADE 2>/dev/null \
    || iptables -t nat -A POSTROUTING -o "$IFACE" -j MASQUERADE

iptables -C FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null \
    || iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

iptables -C FORWARD -i virbr0 -o "$IFACE" -j ACCEPT 2>/dev/null \
    || iptables -A FORWARD -i virbr0 -o "$IFACE" -j ACCEPT

# --- persist iptables rules ---
if command -v netfilter-persistent &>/dev/null; then
    netfilter-persistent save
else
    echo "iptables-persistent not installed — rules will be lost on reboot."
    echo "Install with: sudo apt install iptables-persistent"
fi

echo ""
echo "Done. NAT is active on virbr0 -> $IFACE"
echo "In GNS3, configure the Cloud node to use the 'virbr0' interface."
