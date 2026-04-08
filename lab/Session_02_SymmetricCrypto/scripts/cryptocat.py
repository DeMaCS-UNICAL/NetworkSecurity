#!/usr/bin/env python3
"""
cryptocat.py - Netcat with AES-256-CBC encryption via openssl enc

Usage:
  Server: python3 cryptocat.py -m server -k <password> <host> <port>
  Client: python3 cryptocat.py -m client -k <password> <host> <port>
"""

import argparse
import socket
import subprocess
import sys
import threading

ALGORITHM = "aes-256-cbc"


def openssl_encrypt(data: bytes, password: str) -> bytes:
    result = subprocess.run(
        ["openssl", "enc", f"-{ALGORITHM}", "-e", "-k", password, "-pbkdf2", "-base64"],
        input=data,
        capture_output=True,
    )
    return result.stdout


def openssl_decrypt(data: bytes, password: str) -> bytes:
    result = subprocess.run(
        ["openssl", "enc", f"-{ALGORITHM}", "-d", "-k", password, "-pbkdf2", "-base64"],
        input=data,
        capture_output=True,
    )
    return result.stdout


def send_loop(sock: socket.socket, password: str):
    """Read from stdin, encrypt, send over socket."""
    for line in sys.stdin:
        encrypted = openssl_encrypt(line.encode(), password)
        sock.sendall(encrypted + b"\n---\n")


def recv_loop(sock: socket.socket, password: str):
    """Receive from socket, decrypt, print to stdout."""
    buf = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
        while b"\n---\n" in buf:
            msg, buf = buf.split(b"\n---\n", 1)
            decrypted = openssl_decrypt(msg, password)
            print(decrypted.decode(), end="", flush=True)


def run(sock: socket.socket, password: str):
    t = threading.Thread(target=recv_loop, args=(sock, password))
    t.start()
    send_loop(sock, password)
    sock.shutdown(socket.SHUT_WR)
    t.join()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", choices=["server", "client"], required=True)
    parser.add_argument("-k", required=True, metavar="password")
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    args = parser.parse_args()

    if args.m == "server":
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((args.host, args.port))
        server_sock.listen(1)
        print(f"[*] Listening on {args.host}:{args.port} ...")
        conn, addr = server_sock.accept()
        print(f"[*] Connection from {addr}")
        run(conn, args.k)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((args.host, args.port))
        print(f"[*] Connected to {args.host}:{args.port}")
        run(sock, args.k)


if __name__ == "__main__":
    main()
