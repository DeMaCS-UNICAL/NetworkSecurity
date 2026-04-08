import ssl, socket, pprint

"""
ES03 — TLS socket client (Alice)

Your task: connect to Bob's TLS server on 10.0.0.20:10443, verify his
certificate using the lab CA, then send a message and print the response.

Requirements:
- Use ca.cert (downloaded from Bob) to verify the server certificate
- Print the server certificate details after connecting
- Send the message: "Hello Bob, this is encrypted with TLS!"
- Print the response

You will need:
    ssl.create_default_context()
    context.check_hostname
    context.wrap_socket()
    conn.getpeercert()

Do NOT look at the solution script until you have a working implementation.

Usage:
    python3 es03_client_blank.py
"""

# --- your code here ---
