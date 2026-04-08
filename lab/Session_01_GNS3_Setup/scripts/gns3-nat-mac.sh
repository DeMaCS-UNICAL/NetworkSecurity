#!/usr/bin/env bash
# gns3-nat-mac.sh — NAT setup for GNS3 lab (macOS Apple Silicon)
#
# Run this script before opening GNS3 after every reboot.
# Virtual interfaces (bridge9, feth0/feth1) do not persist across reboots.
#
# Usage: sudo ./gns3-nat-mac.sh

set -euo pipefail

BRIDGE="bridge9"
BRIDGE_IP="192.168.122.1"
BRIDGE_MASK="255.255.255.0"
NAT_NET="192.168.122.0/24"
FETH_A="feth0"
FETH_B="feth1"

# --- detect internet-facing interface ---
IFACE=$(route get default | awk '/interface:/ {print $2}')
if [[ -z "$IFACE" ]]; then
    echo "ERROR: could not detect default network interface" >&2
    exit 1
fi
echo "Using interface: $IFACE"

# --- virtual bridge ---
ifconfig "$BRIDGE" create 2>/dev/null || true
ifconfig "$BRIDGE" "$BRIDGE_IP" netmask "$BRIDGE_MASK" up

# --- virtual ethernet pair ---
ifconfig "$FETH_A" create 2>/dev/null || true
ifconfig "$FETH_B" create 2>/dev/null || true
ifconfig "$FETH_A" peer "$FETH_B" 2>/dev/null || true
ifconfig "$FETH_A" up
ifconfig "$FETH_B" up
ifconfig "$BRIDGE" addm "$FETH_A" 2>/dev/null || true
ifconfig "$BRIDGE" up

# --- IP forwarding ---
sysctl -w net.inet.ip.forwarding=1

# --- NAT with pf ---
echo "nat on $IFACE from $NAT_NET to any -> ($IFACE)" | pfctl -N -f -
pfctl -e 2>/dev/null || true   # "already enabled" is fine

echo ""
echo "Done. NAT is active on $BRIDGE ($BRIDGE_IP) -> $IFACE"
echo "In GNS3, configure the Cloud node to use the '$BRIDGE' interface."
