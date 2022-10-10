from scapy.all import *
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
console=Console()

message_crypted = "Q29tcGxpbWVudGksIGFycCBzcG9vZmluZyBhbmRhdG8gYSBidW9uIGZpbmUK\n"
message_clear = "Hi, the password is: NS_ArpSpoofingKey and the cypher algorithm is pbkdf2\n"
def main(ip_src_h1: str, ip_dst_h2: str, src_port: int=1234, dst_port: int=4444):
    with console.status("Sending Packages..."):
        eth=Ether()/IP(src=ip_src_h1, dst=ip_dst_h2)
        ptk=eth/UDP(sport=src_port,dport=dst_port)/Raw(load=message_crypted)

        ethkey=Ether()/IP(dst=ip_dst_h2)
        ptkkey=ethkey/UDP(sport=src_port,dport=dst_port)/Raw(load=message_clear)

        arr=[ptkkey,ptk]

        sendp(arr, loop=1, inter=5)


if __name__ == "__main__":
    typer.run(main)