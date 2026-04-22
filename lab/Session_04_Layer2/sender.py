"""
sender.py — run on Alice (10.0.0.10)
Simulates Alice sending encrypted UDP traffic to Bob.
Alternates between a cleartext packet (containing the decryption key)
and an encrypted one, every 5 seconds.

Resolves Bob's MAC via ARP before each send — simulating real host behavior.
If ARP fails (CAM full, no reply), falls back to broadcast, which is exactly
when MAC flooding makes the traffic visible to an attacker.

Usage:
    sudo python3 sender.py
    sudo python3 sender.py --src-ip 10.0.0.10 --dst-ip 10.0.0.20
"""

from scapy.all import *
import typer
import time
from rich.console import Console

console = Console()

MESSAGE_CLEAR = (
    "Hi, the password is: NS_ArpSpoofingKey and the cypher algorithm is -aes-256-cbc\n"
)
MESSAGE_ENCRYPTED = "U2FsdGVkX1+c2RE/wElzOwY9mnfmjc7jWi6YptOfzZKOZAWFjtRcnZIwItUw8SZwJjkyJILJJ3j0G/TEJTA4VhkYCPRTRqv78JhZGZU7Efc=\n"


def _resolve_mac(
    dst_ip: str, src_ip: str, iface: str = "enp2s0", timeout: int = 2
) -> str:
    ans = srp1(
        Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(op=1, psrc=src_ip, pdst=dst_ip),
        iface=iface,
        timeout=timeout,
        verbose=0,
    )
    if ans:
        return ans[ARP].hwsrc
    console.print("[yellow]ARP timeout — usando broadcast (CAM piena?)[/yellow]")
    return "ff:ff:ff:ff:ff:ff"


def main(
    src_ip: str = "10.0.0.10",
    dst_ip: str = "10.0.0.20",
    src_port: int = 1234,
    dst_port: int = 4444,
    iface: str = "enp2s0",
):
    console.print(
        f"[cyan]Sending from {src_ip} to {dst_ip} (UDP {src_port} -> {dst_port}) iface={iface}[/cyan]"
    )
    console.print("[yellow]Press Ctrl+C to stop.[/yellow]")
    console.print(f"[cyan]Resolving MAC for {dst_ip}...[/cyan]")
    dst_mac = None
    while dst_mac is None or dst_mac == "ff:ff:ff:ff:ff:ff":
        dst_mac = _resolve_mac(dst_ip, src_ip, iface=iface)
        if dst_mac == "ff:ff:ff:ff:ff:ff":
            console.print("[yellow]ARP fallito, riprovo...[/yellow]")
            time.sleep(1)
    console.print(f"[green]MAC di Bob: {dst_mac}[/green]")

    with console.status("Sending packets..."):
        while True:
            for payload in (MESSAGE_CLEAR, MESSAGE_ENCRYPTED):
                pkt = (
                    Ether(src=get_if_hwaddr(iface), dst=dst_mac)
                    / IP(src=src_ip, dst=dst_ip)
                    / UDP(sport=src_port, dport=dst_port)
                    / Raw(load=payload)
                )
                sendp(pkt, iface=iface, verbose=0)
            time.sleep(5)


if __name__ == "__main__":
    typer.run(main)
