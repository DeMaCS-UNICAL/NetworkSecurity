from scapy.all import *

eth=Ether()/IP(src='10.0.0.2', dst='10.0.0.3')
ptk=eth/UDP(sport=1234,dport=4444)/Raw(load='U2FsdGVkX18pKUHyDYmVFruNUjEIsviM5SYynFxCPKUBzAqkl9Fj1lKchwtu3dMUWK/Gm2VH7bBsHyMj3i35Aw==')

ethkey=Ether()/IP(dst='10.0.0.3')
ptkkey=ethkey/UDP(sport=1234,dport=4444)/Raw(load='Hi, the key is: NS2021_MacFloodingKey')

arr=[ptkkey,ptk]

sendp(arr, loop=1, inter=5)
