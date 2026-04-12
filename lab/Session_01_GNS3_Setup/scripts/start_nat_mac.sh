#!/bin/bash
set -e

BRIDGE="bridge9"
FETH0="feth0"
FETH1="feth1"
BRIDGE_IP="192.168.122.1"
FETH1_IP="192.168.122.254"
SUBNET="192.168.122.0/24"
WAN_IF=$(route get default 2>/dev/null | awk '/interface:/ {print $2}')
if [[ -z "$WAN_IF" ]]; then
    echo "ERROR: could not detect default network interface" >&2
    exit 1
fi

echo "[1/5] Creating feth pair (WAN interface: $WAN_IF)..."
sudo ifconfig $FETH0 create 2>/dev/null || true
sudo ifconfig $FETH1 create 2>/dev/null || true
sudo ifconfig $FETH0 peer $FETH1 2>/dev/null || true  
sudo ifconfig $FETH0 up
sudo ifconfig $FETH1 $FETH1_IP netmask 255.255.255.0 up

echo "[2/5] Creating bridge and adding feth0 as member..."
sudo ifconfig $BRIDGE create 2>/dev/null || true
sudo ifconfig $BRIDGE $BRIDGE_IP netmask 255.255.255.0 up
sudo ifconfig $BRIDGE addm $FETH0 2>/dev/null || true   

echo "[3/5] Fixing route — pointing 192.168.122.0/24 to bridge9..."
sudo route delete -net $SUBNET 2>/dev/null || true
sudo route add -net $SUBNET -interface $BRIDGE

echo "[4/5] Enabling IP forwarding..."
sudo sysctl -w net.inet.ip.forwarding=1
sudo sysctl -w net.inet.icmp.bmcastecho=1

echo "[5/5] Loading NAT rule via pf (interface: $WAN_IF)..."
sudo pfctl -F all 2>/dev/null || true
echo "nat on $WAN_IF from $SUBNET to any -> ($WAN_IF)" | sudo pfctl -f - -e 2>/dev/null || true

echo ""
echo "=== GNS3 NAT ready ==="
echo "  Bridge : $BRIDGE -> $BRIDGE_IP"
echo "  feth0  : bridge member"
echo "  feth1  : GNS3 Cloud node interface (dummy IP: $FETH1_IP)"
echo "  NAT    : $SUBNET -> $WAN_IF"
echo ""
echo "In GNS3: Cloud node must be connected to feth1 (not bridge9)"
echo ""

STATUS=$(ifconfig $BRIDGE | grep "status:" | awk '{print $2}')
if [ "$STATUS" = "active" ]; then
    echo "bridge9 is active"
else
    echo "bridge9 is NOT active — check feth0 membership"
fi

PF_NAT=$(sudo pfctl -s nat 2>/dev/null | grep "nat on")
if [ -n "$PF_NAT" ]; then
    echo "pf NAT rule loaded: $PF_NAT"
else
    echo "pf NAT rule NOT loaded"
fi

FORWARD=$(sysctl -n net.inet.ip.forwarding)
if [ "$FORWARD" = "1" ]; then
    echo "IP forwarding enabled"
else
    echo "IP forwarding NOT enabled"
fi