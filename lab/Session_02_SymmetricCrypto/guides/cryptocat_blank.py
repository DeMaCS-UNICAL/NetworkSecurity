#!/usr/bin/env python3
"""
cryptocat_blank.py — encrypted chat channel (student version)

Your task: fill in the ??? placeholders in openssl_encrypt and openssl_decrypt.
The openssl command you need is the same one you used in Exercise 1.

Usage (once complete):
  Server:  python3 cryptocat_blank.py 0.0.0.0 9999 --mode server --key mysecretkey
  Client:  python3 cryptocat_blank.py 10.0.0.20 9999 --mode client --key mysecretkey
"""

import socket
import threading
import argparse
import subprocess


def openssl_encrypt(message, key):
    cmd = (
        f"echo {message!r} | "
        f"openssl enc ???"          # fill in the flags: cipher, encoding, key derivation, password
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


def openssl_decrypt(ciphertext, key):
    cmd = (
        f"echo {ciphertext!r} | "
        f"openssl enc ???"          # fill in the flags: direction, cipher, encoding, key derivation, password
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return "[decryption failed — wrong key?]"
    return result.stdout.strip()


def receive_loop(conn, key):
    """Read lines from the socket, decrypt and print each one."""
    buf = ""
    while True:
        try:
            data = conn.recv(4096).decode("utf-8", errors="replace")
        except OSError:
            break
        if not data:
            break
        buf += data
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            plaintext = openssl_decrypt(line, key)
            print(f"\r[received] {plaintext}")
            print("> ", end="", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Encrypted chat channel")
    parser.add_argument("host", help="Remote host IP (ignored in server mode)")
    parser.add_argument("port", type=int, help="TCP port")
    parser.add_argument("--mode", choices=["server", "client"], required=True)
    parser.add_argument("--key", required=True, help="Shared encryption key")
    args = parser.parse_args()

    if args.mode == "server":
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", args.port))
        srv.listen(1)
        print(f"[*] Listening on port {args.port} ...")
        conn, addr = srv.accept()
        print(f"[*] Connection from {addr[0]}")
        srv.close()
    else:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[*] Connecting to {args.host}:{args.port} ...")
        conn.connect((args.host, args.port))
        print(f"[*] Connected.")

    t = threading.Thread(target=receive_loop, args=(conn, args.key), daemon=True)
    t.start()

    print("[*] Type a message and press Enter. Ctrl-C to quit.\n")

    try:
        while True:
            print("> ", end="", flush=True)
            msg = input()
            encrypted = openssl_encrypt(msg, args.key)
            conn.sendall((encrypted + "\n").encode())
    except (EOFError, KeyboardInterrupt):
        print("\n[*] Closing connection.")
        conn.close()


if __name__ == "__main__":
    main()
