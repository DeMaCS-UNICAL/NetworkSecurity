import ssl, socket

"""
ES03 — TLS socket server (Bob)

Your task: implement a TLS echo server that listens on port 10443.

Requirements:
- Load the server certificate and private key from ~/lab03/cert/
- Accept one TLS connection from Alice
- For each message received, print it and send back "Echo: <message>"
- Exit cleanly when the client closes the connection

You will need:
    ssl.create_default_context()
    ssl.Purpose
    context.load_cert_chain()
    context.wrap_socket()
    socket.socket()

Do NOT look at the solution script until you have a working implementation.

Usage:
    python3 es03_server_blank.py
"""

# --- your code here ---
