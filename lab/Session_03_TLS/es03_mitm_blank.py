import ssl, socket, threading, os, subprocess

"""
ES03 — TLS MITM proxy (Darth)

Darth intercepts the connection between Alice (10.0.0.10) and Bob (10.0.0.20).

How it works:
- Darth listens on port 10443 (Alice connects to Darth thinking it is Bob)
- For each connection from Alice, Darth opens a separate TLS connection to Bob
- Darth forwards messages in both directions, reading the plaintext in the middle

To fool Alice, Darth presents a fake certificate for bob.lab signed by his own CA.
This script generates Darth's CA and fake certificate automatically, then starts
the proxy.

Your tasks:
1. Generate Darth's CA key and self-signed certificate (use subprocess + openssl)
2. Generate a fake server key and certificate for bob.lab / IP:10.0.0.20,
   signed by Darth's CA
3. Build a server-side SSL context using the fake certificate
4. Build a client-side SSL context to connect to Bob — for now, disable
   certificate verification (ssl.CERT_NONE) so Darth can reach Bob regardless
5. Accept a connection from Alice, wrap it with the fake cert (server_side=True)
6. Open a connection to Bob (10.0.0.20:10443), wrap it as a TLS client
7. Forward data in both directions using two threads

You will need:
    ssl.create_default_context()
    ssl.Purpose
    ssl.CERT_NONE
    context.load_cert_chain()
    context.wrap_socket()
    threading.Thread()

Do NOT look at the solution script until you have a working implementation.

Usage:
    python3 es03_mitm_blank.py
    # then run es03_client_blank.py on Alice (pointing to Darth's IP instead of Bob's)
"""

DARTH_IP   = '0.0.0.0'
BOB_IP     = '10.0.0.20'
LISTEN_PORT = 10443
BOB_PORT    = 10443
WORKDIR     = os.path.expanduser('~/lab03/darth')

os.makedirs(WORKDIR, exist_ok=True)

# --- your code here ---
