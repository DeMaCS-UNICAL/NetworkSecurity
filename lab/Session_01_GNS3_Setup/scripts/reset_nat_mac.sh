#!/usr/bin/env bash
set -euo pipefail

ifconfig bridge9 destroy 2>/dev/null && echo "bridge9 destroyed" || echo "bridge9 not found"
ifconfig feth0 destroy 2>/dev/null && echo "feth0 destroyed"   || echo "feth0 not found"
ifconfig feth1 destroy 2>/dev/null && echo "feth1 destroyed"   || echo "feth1 not found"

sudo pfctl -F nat 2>/dev/null && echo "NAT rules flushed" || echo "NAT flush failed (ok if pf was not running)"

echo "Done. Run start_nat_mac.sh to recreate."
