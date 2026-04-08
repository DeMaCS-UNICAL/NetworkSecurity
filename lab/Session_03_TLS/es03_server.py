import ssl, socket, os

"""
ES03 — TLS socket server (Bob) — SOLUTION
"""

CERT_DIR = os.environ.get("CERT_DIR", os.path.join(os.path.expanduser("~"), "lab03", "cert"))
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(
    certfile=os.path.join(CERT_DIR, "server.cert"),
    keyfile=os.path.join(CERT_DIR, "server.key"),
)

raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
raw_socket.bind(('0.0.0.0', 10443))
raw_socket.listen(5)
print("Waiting for connection...")

conn_raw, addr = raw_socket.accept()
conn = context.wrap_socket(conn_raw, server_side=True)
print(f"Connected: {addr}")

while True:
    data = conn.recv(1024)
    if not data:
        break
    msg = data.decode('utf-8').strip()
    print(f"Received: {msg}")
    conn.send(f"Echo: {msg}".encode('utf-8'))
