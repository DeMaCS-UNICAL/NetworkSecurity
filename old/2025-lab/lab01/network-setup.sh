#!/bin/bash

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables for summary
LIBVIRTD_STATUS=""
VIRTLOGD_STATUS=""
VNET_STATUS=""
INTERFACE_NAME=""
IPTABLES_RULES_COUNT=0

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}This script must be run as root (with sudo)${NC}"
    exit 1
fi

# Function to check and start a service
check_service() {
    local service_name=$1
    echo -e "${BLUE}Checking $service_name status...${NC}"
    
    if ! systemctl is-active --quiet "$service_name"; then
        echo -e "${YELLOW}$service_name is not running. Starting it...${NC}"
        systemctl start "$service_name"
        
        # Verify the service started successfully
        if systemctl is-active --quiet "$service_name"; then
            echo -e "${GREEN}✓ $service_name started successfully${NC}"
            [[ $service_name == "libvirtd.service" ]] && LIBVIRTD_STATUS="Running"
            [[ $service_name == "virtlogd.service" ]] && VIRTLOGD_STATUS="Running"
        else
            echo -e "${RED}✗ Failed to start $service_name${NC}"
            [[ $service_name == "libvirtd.service" ]] && LIBVIRTD_STATUS="Failed"
            [[ $service_name == "virtlogd.service" ]] && VIRTLOGD_STATUS="Failed"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ $service_name is already running${NC}"
        [[ $service_name == "libvirtd.service" ]] && LIBVIRTD_STATUS="Running"
        [[ $service_name == "virtlogd.service" ]] && VIRTLOGD_STATUS="Running"
    fi
}

# Function to check and start virtual network
check_virtual_network() {
    echo -e "${BLUE}Checking virtual network status...${NC}"
    
    # Verifica se la rete default esiste
    if ! virsh net-list --all | grep -q "default"; then
        echo -e "${RED}Network 'default' non trovata. Creazione...${NC}"
        virsh net-define /etc/libvirt/qemu/networks/default.xml
    fi

    # Verifica se la rete è attiva
    if ! virsh net-list --all | grep -q "default.*active"; then
        echo -e "${YELLOW}Virtual network non attiva. Avvio...${NC}"
        
        # Attendi che libvirtd sia completamente inizializzato
        sleep 2
        
        # Prova ad avviare la rete con più tentativi
        for i in {1..3}; do
            if virsh net-start default; then
                echo -e "${GREEN}✓ Virtual network avviata con successo${NC}"
                VNET_STATUS="Running"
                return 0
            else
                echo -e "${YELLOW}Tentativo $i fallito. Attendo...${NC}"
                sleep 2
            fi
        done
        
        echo -e "${RED}✗ Impossibile avviare la rete virtuale dopo 3 tentativi${NC}"
        echo -e "${YELLOW}Prova ad eseguire 'sudo virsh net-start default' manualmente${NC}"
        VNET_STATUS="Failed"
        return 1
    else
        echo -e "${GREEN}✓ Virtual network già attiva${NC}"
        VNET_STATUS="Running"
        return 0
    fi
}

# Function to find the internet-connected interface
find_internet_interface() {
    # Looking for an interface with a default route
    local interface=$(ip route | grep '^default' | awk '{print $5}' | head -n1)
    
    if [ -z "$interface" ]; then
        echo -e "${RED}✗ Could not find an interface with internet connection${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Found internet interface: $interface${NC}"
    INTERFACE_NAME="$interface"
    return 0
}

# Function to check if an iptables rule exists and show it
check_iptables_rule() {
    local table=$1
    local rule=$2
    
    # First check if rule exists
    if [ "$table" = "nat" ]; then
        iptables -t nat -C $rule 2>/dev/null
        if [ $? -eq 0 ]; then
            # Rule exists, get and show the full rule
            echo -e "${YELLOW}→ Existing $table rule:${NC}"
            iptables -t nat -S POSTROUTING | grep -- "-j MASQUERADE" | while read -r line; do
                echo -e "  ${BLUE}$line${NC}"
            done
            return 0
        fi
    else
        iptables -C $rule 2>/dev/null
        if [ $? -eq 0 ]; then
            # Rule exists, get and show the full rule
            echo -e "${YELLOW}→ Existing FORWARD rule:${NC}"
            iptables -S FORWARD | grep -- "$rule" | while read -r line; do
                echo -e "  ${BLUE}$line${NC}"
            done
            return 0
        fi
    fi
    return 1
}

# Function to remove existing iptables rules
remove_existing_rules() {
    local interface=$1
    echo -e "\n${BLUE}Removing existing iptables rules...${NC}"

    # Remove only our specific NAT rule if exists
    # Find the exact rule without impacting Docker rules
    iptables-save -t nat | grep "^-A POSTROUTING -o $interface -j MASQUERADE$" > /dev/null
    if [ $? -eq 0 ]; then
        echo -e "${YELLOW}Removing NAT rule for $interface...${NC}"
        iptables -t nat -D POSTROUTING -o "$interface" -j MASQUERADE
    fi

    # Remove established connections rule if exists
    if check_iptables_rule "filter" "FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT" &>/dev/null; then
        echo -e "${YELLOW}Removing established connections rule...${NC}"
        iptables -D FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    fi

    # Remove our specific forwarding rule if exists
    iptables-save | grep "^-A FORWARD -i virbr0 -o $interface -j ACCEPT$" > /dev/null
    if [ $? -eq 0 ]; then
        echo -e "${YELLOW}Removing forwarding rule for virbr0...${NC}"
        iptables -D FORWARD -i virbr0 -o "$interface" -j ACCEPT
    fi

    echo -e "${GREEN}✓ Selected rules removed${NC}\n"
}

# Function to set up iptables rules
setup_iptables() {
    local interface=$1
    local force=$2

    echo -e "${BLUE}Checking and setting up iptables rules for interface $interface...${NC}"
    echo -e "${YELLOW}Force mode: $force${NC}"   # Debug output
    
    # If force is enabled, remove existing rules first
    if [ "$force" = "true" ]; then
        remove_existing_rules "$interface"
    fi

    echo -e "\n${BLUE}Checking NAT rule:${NC}"
    # Check and add NAT rule
    if ! check_iptables_rule "nat" "POSTROUTING -o $interface -j MASQUERADE"; then
        if iptables -t nat -A POSTROUTING -o "$interface" -j MASQUERADE; then
            echo -e "${GREEN}✓ Added new NAT rule${NC}"
            ((IPTABLES_RULES_COUNT++))
        else
            echo -e "${RED}✗ Failed to add NAT rule${NC}"
            exit 1
        fi
    fi
    
    echo -e "\n${BLUE}Checking established connections rule:${NC}"
    # Check and add established connections rule
    if ! check_iptables_rule "filter" "FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT"; then
        if iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT; then
            echo -e "${GREEN}✓ Added new established connections rule${NC}"
            ((IPTABLES_RULES_COUNT++))
        else
            echo -e "${RED}✗ Failed to add established connections rule${NC}"
            exit 1
        fi
    fi
    
    echo -e "\n${BLUE}Checking forwarding rule:${NC}"
    # Check and add forwarding rule
    if ! check_iptables_rule "filter" "FORWARD -i virbr0 -o $interface -j ACCEPT"; then
        if iptables -A FORWARD -i virbr0 -o "$interface" -j ACCEPT; then
            echo -e "${GREEN}✓ Added new forwarding rule${NC}"
            ((IPTABLES_RULES_COUNT++))
        else
            echo -e "${RED}✗ Failed to add forwarding rule${NC}"
            exit 1
        fi
    fi
    
    echo # Add a newline for spacing
    if [ $IPTABLES_RULES_COUNT -gt 0 ]; then
        echo -e "${GREEN}✓ Added $IPTABLES_RULES_COUNT new iptables rules${NC}"
    else
        echo -e "${BLUE}ℹ All required iptables rules were already in place${NC}"
    fi
}

# Function to show summary
show_summary() {
    local setup_successful=true

    # Check if virbr0 exists
    if ! ip link show virbr0 &>/dev/null; then
        setup_successful=false
        echo -e "${RED}Error: Virtual bridge interface (virbr0) does not exist${NC}"
        return 1
    fi

    echo -e "\n${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          Configuration Summary         ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    
    echo -e "\n${BLUE}Services Status:${NC}"
    echo -e "  libvirtd: ${GREEN}$LIBVIRTD_STATUS${NC}"
    echo -e "  virtlogd: ${GREEN}$VIRTLOGD_STATUS${NC}"
    
    echo -e "\n${BLUE}Network Configuration:${NC}"
    echo -e "  Virtual Network: ${GREEN}$VNET_STATUS${NC}"
    echo -e "  Internet Interface: ${GREEN}$INTERFACE_NAME${NC}"
    
    echo -e "\n${BLUE}IPTables Configuration:${NC}"
    echo -e "  Rules Added: ${GREEN}$IPTABLES_RULES_COUNT${NC}"
    
    # Get current IP forwarding status
    local ip_forward=$(cat /proc/sys/net/ipv4/ip_forward)
    echo -e "  IP Forwarding: ${GREEN}$( [[ $ip_forward == 1 ]] && echo "Enabled" || echo "Disabled" )${NC}"
    
    # Show current iptables rules count
    local nat_rules=$(iptables -t nat -L | grep -c '^MASQUERADE')
    local forward_rules=$(iptables -L FORWARD | grep -c 'ACCEPT')
    echo -e "  Total NAT Rules: ${GREEN}$nat_rules${NC}"
    echo -e "  Total Forward Rules: ${GREEN}$forward_rules${NC}"
    
    echo -e "\n${BLUE}Additional Information:${NC}"
    # Check if we can get virbr0 IP
    local virbr0_ip=$(ip addr show virbr0 2>/dev/null | grep 'inet ' | awk '{print $2}')
    if [ -n "$virbr0_ip" ]; then
        echo -e "  Virtual Bridge IP: ${GREEN}$virbr0_ip${NC}"
    else
        echo -e "  Virtual Bridge IP: ${RED}Not available${NC}"
        setup_successful=false
    fi

    # Check if we can get interface IP
    local interface_ip=$(ip addr show $INTERFACE_NAME 2>/dev/null | grep 'inet ' | awk '{print $2}')
    if [ -n "$interface_ip" ]; then
        echo -e "  Interface IP: ${GREEN}$interface_ip${NC}"
    else
        echo -e "  Interface IP: ${RED}Not available${NC}"
        setup_successful=false
    fi

    echo # Add a newline for spacing
    
    if $setup_successful; then
        echo -e "${GREEN}Setup completed successfully!${NC}\n"
    fi
}

# Parse command line arguments
FORCE_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE_MODE=true
            shift # past argument
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${NC}"
            echo "Usage: $0 [-f|--force]"
            exit 1
            ;;
    esac
done

# Print banner
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Network Setup Configuration       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# Main script execution
echo -e "${BLUE}Starting network setup...${NC}"

# Check and start required services
check_service "libvirtd.service"
check_service "virtlogd.service"

# Check and start virtual network
check_virtual_network

# Find internet interface
internet_interface=$(ip route | grep '^default' | awk '{print $5}' | head -n1)
if [ -n "$internet_interface" ]; then
    echo -e "${GREEN}✓ Using interface: $internet_interface${NC}"
    INTERFACE_NAME="$internet_interface"
    # Set up iptables rules
    setup_iptables "$internet_interface" $FORCE_MODE      # Rimosso le virgolette
    # Show configuration summary
    show_summary
else
    echo -e "${RED}✗ Failed to find internet interface${NC}"
    exit 1
fi


##   -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
##   -A POSTROUTING -s 172.17.0.2/32 -d 172.17.0.2/32 -p tcp -m tcp --dport 8000 -j MASQUERADE
##   -A POSTROUTING -s 172.17.0.2/32 -d 172.17.0.2/32 -p tcp -m tcp --dport 9443 -j MASQUERADE