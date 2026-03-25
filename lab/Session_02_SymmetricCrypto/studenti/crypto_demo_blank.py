#!/usr/bin/env python3
"""
crypto_demo_blank.py — AES encryption demo (student version)

Your task: fill in the ??? placeholders in each experiment.
Read the comments carefully — they tell you what each line should do.

Usage:
  python3 crypto_demo_blank.py 1
  python3 crypto_demo_blank.py 2
  python3 crypto_demo_blank.py 3
"""

import sys
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


# ─────────────────────────────────────────────────────────────
# Experiment 1 — Basic encrypt / decrypt
# ─────────────────────────────────────────────────────────────

def experiment1():
    print("=" * 60)
    print("Experiment 1 — Basic AES-256-CBC encrypt / decrypt")
    print("=" * 60)

    key = get_random_bytes(32)   # 256-bit key
    iv  = get_random_bytes(16)   # 128-bit IV

    print(f"\nKey (hex) : {key.hex()}")
    print(f"IV  (hex) : {iv.hex()}")

    plaintext = b"Hello from Python!"

    # Create a cipher object and encrypt.
    # AES.new() takes: key, mode, iv
    # Which mode should you use for CBC?  →  AES.MODE_???
    cipher    = AES.new(key, ???, iv)
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

    print(f"\nPlaintext  : {plaintext.decode()}")
    print(f"Ciphertext : {base64.b64encode(ciphertext).decode()}")

    # Decrypt — you must create a NEW cipher object with the same key and IV.
    # Which mode?  →  AES.MODE_???
    cipher2   = AES.new(key, ???, iv)
    recovered = unpad(cipher2.decrypt(ciphertext), AES.block_size)

    print(f"Recovered  : {recovered.decode()}")

    print("\n→ Run this script again. The ciphertext will be different")
    print("  each time because a new random key and IV are generated.")


# ─────────────────────────────────────────────────────────────
# Experiment 2 — IV reuse attack
# ─────────────────────────────────────────────────────────────

def experiment2():
    print("=" * 60)
    print("Experiment 2 — Why the IV must be random and unique")
    print("=" * 60)
    print("""
Scenario: Alice always uses the same key and the same fixed IV
to encrypt her messages (a common mistake in naive implementations).

An attacker intercepts two ciphertexts.
Even without decrypting, the attacker can learn things:

  - If two ciphertexts are identical → the plaintexts are identical
  - If two ciphertexts share a common prefix → the plaintexts
    share a common prefix

With a fresh random IV each time, this leaks nothing.
""")

    key      = b"mysecretkey12345" * 2   # 32 bytes fixed key
    fixed_iv = b"0000000000000000"       # 16 bytes — this is the BAD choice

    # Generate two random IVs for the good case.
    # Use get_random_bytes() with the correct size.
    rand_iv1 = ???
    rand_iv2 = ???

    msg_a = b"Transfer 100 EUR"
    msg_b = b"Transfer 100 EUR"   # same message sent twice

    # With fixed IV: same plaintext → same ciphertext
    c_fixed_a = AES.new(key, AES.MODE_CBC, fixed_iv).encrypt(pad(msg_a, 16))
    c_fixed_b = AES.new(key, AES.MODE_CBC, fixed_iv).encrypt(pad(msg_b, 16))

    # With random IV: same plaintext → different ciphertext
    c_rand_a = AES.new(key, AES.MODE_CBC, rand_iv1).encrypt(pad(msg_a, 16))
    c_rand_b = AES.new(key, AES.MODE_CBC, rand_iv2).encrypt(pad(msg_b, 16))

    print("── Fixed IV (bad) ──────────────────────────────────────")
    print(f"  Ciphertext A : {base64.b64encode(c_fixed_a).decode()}")
    print(f"  Ciphertext B : {base64.b64encode(c_fixed_b).decode()}")
    print(f"  Identical?   : {c_fixed_a == c_fixed_b}  ← attacker knows msg_a == msg_b")

    print("\n── Random IV (good) ────────────────────────────────────")
    print(f"  Ciphertext A : {base64.b64encode(c_rand_a).decode()}")
    print(f"  Ciphertext B : {base64.b64encode(c_rand_b).decode()}")
    print(f"  Identical?   : {c_rand_a == c_rand_b}  ← attacker learns nothing")

    print("\n→ Always generate a fresh random IV for each encryption.")
    print("  The IV does not need to be secret — send it alongside the ciphertext.")


# ─────────────────────────────────────────────────────────────
# Experiment 3 — ECB vs CBC
# ─────────────────────────────────────────────────────────────

def experiment3():
    print("=" * 60)
    print("Experiment 3 — ECB vs CBC mode")
    print("=" * 60)
    print("""
ECB (Electronic Codebook): each 16-byte block is encrypted
independently. Identical plaintext blocks → identical ciphertext
blocks. Patterns in the plaintext leak into the ciphertext.

CBC (Cipher Block Chaining): each block is XORed with the
previous ciphertext block before encryption. Identical plaintext
blocks produce different ciphertext blocks. No patterns leak.
""")

    key = get_random_bytes(32)
    iv  = get_random_bytes(16)

    # Message with four identical 16-byte blocks
    msg = b"AAAAAAAAAAAAAAAA" * 4
    print(f"Plaintext: {'AAAAAAAAAAAAAAAA ' * 4}(4 identical blocks of 16 bytes)")

    # Encrypt with ECB — does not use an IV.
    # Which mode constant?  →  AES.MODE_???
    ecb = AES.new(key, ???).encrypt(msg)

    # Encrypt with CBC — uses the IV.
    # Which mode constant?  →  AES.MODE_???
    cbc = AES.new(key, ???, iv).encrypt(msg)

    # Split into 16-byte blocks
    ecb_blocks = [ecb[i:i+16].hex() for i in range(0, len(ecb), 16)]
    cbc_blocks = [cbc[i:i+16].hex() for i in range(0, len(cbc), 16)]

    print("\nECB ciphertext blocks:")
    for i, b in enumerate(ecb_blocks):
        print(f"  Block {i+1}: {b}")

    print("\nCBC ciphertext blocks:")
    for i, b in enumerate(cbc_blocks):
        print(f"  Block {i+1}: {b}")

    ecb_all_same = len(set(ecb_blocks)) == 1
    cbc_all_same = len(set(cbc_blocks)) == 1

    print(f"\nECB — all blocks identical? {ecb_all_same}  ← attacker sees the pattern")
    print(f"CBC — all blocks identical? {cbc_all_same}  ← no pattern visible")
    print("\n→ Never use ECB in practice. Use CBC (or AES-GCM for authenticated encryption).")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

EXPERIMENTS = {
    "1": experiment1,
    "2": experiment2,
    "3": experiment3,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in EXPERIMENTS:
        print("Usage: python3 crypto_demo_blank.py <1|2|3>")
        print("  1 — Basic AES-256-CBC encrypt/decrypt")
        print("  2 — IV reuse attack")
        print("  3 — ECB vs CBC mode comparison")
        sys.exit(1)

    EXPERIMENTS[sys.argv[1]]()
