from scapy.all import *

eth=Ether()/IP(src='10.0.0.2', dst='10.0.0.3')
ptk=eth/UDP(sport=1234,dport=4444)/Raw(load='U2FsdGVkX1+6rWRHJuyvlTS0M7fqM4j0a0/wOIAUdQwUVSKAJw3QnmsszO/q2cU3AYI39PNpZJXhpNm3HyYCQA==')

ethkey=Ether()/IP(dst='10.0.0.3')
ptkkey=ethkey/UDP(sport=1234,dport=4444)/Raw(load='Hi, the key is: NS_ArpSpoofingKey')

arr=[ptkkey,ptk]

sendp(arr, loop=1, inter=5)
