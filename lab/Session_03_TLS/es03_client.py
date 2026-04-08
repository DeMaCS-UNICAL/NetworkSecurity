import ssl, socket, os, pprint

"""
ES03 — TLS socket client (Alice) — SOLUTION
"""

CA_FILE = os.environ.get("CA_CERT", os.path.join(os.path.expanduser("~"), "lab03", "cert", "ca.cert"))
context = ssl.create_default_context(cafile=CA_FILE)
context.check_hostname = False  # connecting by IP, not hostname

conn = context.wrap_socket(socket.socket(), server_hostname='bob.lab')
conn.connect(("10.0.0.20", 10443))

print("Connected. Server certificate:")
pprint.pprint(conn.getpeercert())

conn.send(b"Hello Bob, this is encrypted with TLS!")
response = conn.recv(1024)
print(f"Response: {response.decode()}")

conn.close()
