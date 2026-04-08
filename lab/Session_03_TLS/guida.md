# Session 03 — Asymmetric Cryptography & TLS

**Network Security Lab · University of Calabria · A.Y. 2025/2026**
**Environment**: GNS3 — Alice `10.0.0.10`, Bob `10.0.0.20`, Darth `10.0.0.30`

---

## Before you start

The GNS3 topology from Session 01 must be running with a **switch** (not a hub — you do not need Darth to sniff this session until ES03).

Verify connectivity on Bob:

```bash
ping -c 2 10.0.0.10    # Alice
ping -c 2 8.8.8.8      # Google DNS
ping -c 2 google.com   # DNS works
```

If any ping fails, fix the network before proceeding.

**Install required tools on Bob**:

```bash
sudo apt update
sudo apt install -y nginx certbot openssl python3-requests python3-certifi
```

**Install required tools on Alice**:

```bash
sudo apt update
sudo apt install -y openssl python3-requests python3-certifi
```

**Serve the lab scripts** from your host machine (same as Lab 02):

```bash
# On your host machine, inside the lab scripts folder
python3 -m http.server 8080
```

Then on Alice:

```bash
wget http://192.168.122.1:8080/es03_client_blank.py
```

And on Bob:

```bash
wget http://192.168.122.1:8080/es03_server_blank.py
```

---

## The problem from Lab 02

In Lab 02, Alice and Bob used this to start CryptoCat:

```bash
python3 cryptocat.py 10.0.0.20 9999 --mode client --key mysecretkey
```

The key `mysecretkey` had to be the same on both sides. But **how did they agree on it**? If they sent it over the network, Darth could have seen it. If they agreed in person, that doesn't scale.

This is the **key distribution problem** — the fundamental limitation of symmetric cryptography. Today's exercises show how asymmetric cryptography and TLS solve it.

---

## Exercise 1 — Generate a CA and a server certificate

### The idea

You are going to be your own Certificate Authority. You will generate a CA key pair, create a self-signed CA certificate, then use it to sign a server certificate for Bob. This is exactly what real CAs do — the only difference is that no one else trusts your CA yet.

**Work on Bob for this entire exercise.**

### 1a — Generate the CA

```bash
mkdir -p ~/lab03/cert && cd ~/lab03/cert
```

Generate the CA private key:

```bash
openssl genrsa -out ca.key 2048
```

> We omit `-aes256` (password protection on the key) to keep the exercise simple. In production, always protect private keys with a passphrase.

Create a config file for the CA certificate. This sets the required extensions (`basicConstraints`, `keyUsage`) that modern OpenSSL and Python 3.13+ enforce:

```bash
cat > ca.ext << 'EOF'
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
CN = LabCA
O = NetworkSecurityLab
C = IT

[v3_ca]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
EOF
```

Create the CA's self-signed certificate (valid 365 days):

```bash
openssl req -new -x509 -days 365 -key ca.key -out ca.cert -config ca.ext
```

Inspect it:

```bash
openssl x509 -in ca.cert -noout -text
```

**Checkpoint**: you should see `Issuer` and `Subject` both containing `LabCA`. The certificate is self-signed — it vouches for itself.

### 1b — Generate the server certificate

Generate the server private key:

```bash
openssl genrsa -out server.key 2048
```

Create a Certificate Signing Request (CSR) — this is what you "submit" to the CA:

```bash
openssl req -new -key server.key -out server.csr -subj "/CN=bob.lab/O=NetworkSecurityLab/C=IT"
```

Add a Subject Alternative Name (SAN) with Bob's IP — required by curl and Python to verify the certificate when connecting by IP:

```bash
echo "subjectAltName=IP:10.0.0.20,DNS:bob.lab" > server.ext
```

Sign the CSR with your CA to produce the server certificate:

```bash
openssl x509 -req -days 365 \
    -in server.csr \
    -CA ca.cert -CAkey ca.key -CAcreateserial \
    -extfile server.ext \
    -out server.cert
```

Verify the chain:

```bash
openssl verify -CAfile ca.cert server.cert
```

**Checkpoint**: output should be `server.cert: OK`.

Inspect the server certificate:

```bash
openssl x509 -in server.cert -noout -text
```

**Checkpoint**: `Issuer` is `LabCA`, `Subject` is `bob.lab`. The CA signed a certificate that says "this public key belongs to bob.lab".

**Question**: who needs the private key (`server.key`)? Who needs the CA certificate (`ca.cert`)?

---

## Exercise 2 — NGINX over HTTPS with your certificate

### The idea

You will configure NGINX on Bob to serve a page over HTTPS using the certificate from Exercise 1. Then you will connect from Alice and observe what happens when a CA is not trusted.

### 2a — Create a minimal website

Still on Bob:

```bash
sudo mkdir -p /var/www/lab03
echo '<h1>Hello from Bob over TLS!</h1>' | sudo tee /var/www/lab03/index.html
```

### 2b — Configure NGINX

Create the NGINX site config:

```bash
sudo tee /etc/nginx/sites-available/lab03 > /dev/null << 'EOF'
server {
    listen 443 ssl;
    server_name bob.lab 10.0.0.20;

    ssl_certificate     /home/ubuntu/lab03/cert/server.cert;
    ssl_certificate_key /home/ubuntu/lab03/cert/server.key;

    root /var/www/lab03;
    location / {
        try_files $uri $uri/ =404;
    }
}
EOF
```

Enable the site and reload:

```bash
sudo ln -s /etc/nginx/sites-available/lab03 /etc/nginx/sites-enabled/lab03
sudo nginx -t && sudo systemctl reload nginx
```

**Checkpoint**: `nginx -t` should print `syntax is ok` and `test is successful`.

### 2c — Connect from Alice

On Alice, try connecting with `curl`:

```bash
curl https://10.0.0.20
```

**Checkpoint**: curl fails with a certificate verification error. The CA that signed Bob's certificate is not in Alice's trust store.

Now tell curl to trust your CA:

```bash
# First, copy ca.cert from Bob to Alice
# On Bob:
python3 -m http.server 5000 --directory ~/lab03/cert
# On Alice:
wget http://10.0.0.20:5000/ca.cert

# Now use it:
curl --cacert ca.cert https://10.0.0.20
```

**Checkpoint**: curl prints `Hello from Bob over TLS!`.

**Question**: the connection was encrypted — but did Alice verify that she was really talking to Bob, or just to someone with a certificate signed by your CA?

### 2d — Inspect the connection

On Alice:

```bash
openssl s_client -connect 10.0.0.20:443 -CAfile ca.cert
```

Look at the output: certificate chain, cipher suite, TLS version.

**Question**: what TLS version is negotiated? What cipher suite? Where is the symmetric session key in all of this?

---

## Exercise 3 — TLS socket in Python

### The idea

You will write a TLS socket server (on Bob) and client (on Alice) in Python. The goal is the same as CryptoCat from Lab 02 — two machines communicating securely — but now the trust is established via certificates, not a hardcoded shared key.

Keep the switch in GNS3 for exercises 3a and 3b.

### 3a — The server (Bob)

Download the blank script:

```bash
wget http://192.168.122.1:8080/es03_server_blank.py
```

Open `es03_server_blank.py` and implement a TLS echo server from scratch. The script contains the requirements and the list of `ssl` functions you will need — no skeleton code is provided.

The certificate files are already on Bob from Exercise 1 (`~/lab03/cert/server.cert` and `~/lab03/cert/server.key`).

Run the server:

```bash
python3 es03_server_blank.py
```

### 3b — The client (Alice)

Alice needs `ca.cert` to verify Bob's certificate. If you did not already download it in ES02:

```bash
# On Bob:
python3 -m http.server 5000 --directory ~/lab03/cert
# On Alice:
wget http://10.0.0.20:5000/ca.cert
```

Download the blank script:

```bash
wget http://192.168.122.1:8080/es03_client_blank.py
```

Open `es03_client_blank.py` and implement the TLS client. Connect to Bob on port 10443, verify his certificate using `ca.cert`, print the certificate details, send a message, and print the response.

Run the client:

```bash
python3 es03_client_blank.py
```

**Checkpoint**: Alice connects, Bob prints "Connected", Alice sees the server certificate printed, then "Response: Echo: Hello Bob, this is encrypted with TLS!".

------------------- SONO ARRIVATA QUI -----------------

### 3c — Darth observes

> **Topology**: replace the switch with a hub in GNS3 so Darth can see Alice↔Bob traffic.

Start a Wireshark capture on Darth, then run 3a and 3b again. Filter: `tcp.port == 10443`.

**Checkpoint**: Darth sees only opaque TLS records — the entire channel is encrypted, not just the message content.

This is different from Lab 02: in CryptoCat, only the application payload was encrypted, but the underlying TCP stream was in plaintext. Darth could still observe protocol metadata, packet sizes, and timing. With TLS, the entire channel is encrypted at the transport level — Darth sees nothing beyond the fact that a TLS connection exists.

The key exchange also works differently: in CryptoCat, `mysecretkey` had to be agreed on in advance. Here, Alice only needed `ca.cert` — a file with no secrets, that could be transferred over any channel.

**Question**: if Darth intercepts `ca.cert`, what can he do with it? What if he intercepts `server.key`?

### 3d — What happens without the CA certificate

On Alice, try connecting without the CA file:

```python
context = ssl.create_default_context()   # uses system CAs only
```

**Checkpoint**: the connection fails with a certificate verification error. The system does not trust your self-signed CA.

This is exactly what your browser does when you visit an HTTPS site with an untrusted or expired certificate.

### 3e — Darth attempts a MITM attack

> **Topology**: the switch can stay in place for this exercise. Unlike ES03c (passive sniffing), this is an **active** MITM — Alice deliberately connects to Darth's IP instead of Bob's. In a real attack, Darth would use ARP poisoning or DNS spoofing to redirect Alice's traffic without her knowledge. Here we simulate that by manually pointing Alice at `10.0.0.30`.
>
> **Start order matters**: launch in this order:
>
> 1. Bob — `es03_server.py` must be listening before Darth starts
> 2. Darth — `es03_mitm_blank.py` connects to Bob at startup; if Bob is down it crashes
> 3. Alice — connect only after both Bob and Darth are ready

So far, TLS has protected Alice and Bob from passive eavesdropping. But what if Darth is more ambitious?

Darth will act as a **transparent TLS proxy**:

- Alice connects to Darth (thinking it is Bob)
- Darth connects to Bob on Alice's behalf
- Darth reads every message in plaintext before forwarding it

To impersonate Bob, Darth generates his own CA and a fake certificate for `bob.lab` / `10.0.0.20`.

Download the blank script on Darth:

```bash
wget http://192.168.122.1:8080/es03_mitm_blank.py
```

Open `es03_mitm_blank.py` and implement the proxy. The script contains the requirements and the list of `ssl` functions you will need.

Run the proxy on Darth:

```bash
python3 es03_mitm_blank.py
```

Then run `es03_client_blank.py` on Alice, but point it to Darth's IP (`10.0.0.30`) instead of Bob's.

**Checkpoint 1**: Alice's connection fails with a certificate verification error. Darth's fake certificate is rejected because Alice does not trust Darth's CA.

Now modify Alice's client to disable certificate verification:

```python
context.verify_mode = ssl.CERT_NONE
```

**Checkpoint 2**: the connection succeeds. Alice and Bob exchange messages normally — but Darth reads every message in plaintext on his terminal.

**Question**: the cryptography worked perfectly throughout this exercise. Darth's certificate was rejected in Checkpoint 1 because of a _trust_ decision, not a mathematical one. Where are trust decisions stored?

> _Hint: think about what Alice would have needed to accept Darth's certificate without error — and how Darth could have made that happen without touching Alice's machine._

**Question**: in Checkpoint 2, Alice disabled certificate verification. What real-world scenario does this resemble? Have you ever clicked "proceed anyway" on a browser certificate warning?

---

## Exercise 4 — A real certificate with Let's Encrypt and DuckDNS

### The idea

In Exercise 1 you were your own CA — but no one else trusts you. Let's Encrypt is a free, publicly trusted CA that issues real certificates automatically. The challenge: to prove you own a domain, Let's Encrypt must verify it. The standard HTTP challenge requires a publicly reachable server on port 80, which is not possible in the GNS3 lab. Instead, you will use the **DNS challenge**: Let's Encrypt asks you to publish a specific TXT record in your domain's DNS, which proves you control the domain without exposing any port.

The flow:

1. Register a free domain on DuckDNS.
2. Run certbot with the DNS-DuckDNS plugin — it automatically publishes the TXT record for you.
3. certbot downloads a signed certificate from Let's Encrypt.
4. Configure NGINX to use it.
5. Connect from Alice — no `--cacert` needed, because Let's Encrypt is already trusted by every OS.

**Work on Bob for this entire exercise.**

### 4a — Configure port forwarding on your host machine

Bob (`10.0.0.20`) is inside the GNS3 network and not directly reachable from outside. You need to forward port 444 from your host machine to Bob.

Find your host machine's university IP:

```bash
# On your host machine (macOS):
ipconfig getifaddr en0
```

Forward incoming connections on port 444 to Bob:

```bash
# On your host machine (macOS) — run once per session:
echo "rdr pass on en0 proto tcp from any to any port 444 -> 10.0.0.20 port 444" | sudo pfctl -ef -
sudo sysctl -w net.inet.ip.forwarding=1
```

> If pfctl complains about an existing ruleset, save the current rules first:
> `sudo pfctl -s nat > /tmp/pf_current.conf` then merge manually.

### 4b — Register a domain on DuckDNS

> This step requires internet access. Bob must be able to reach `duckdns.org`.

1. Open a browser on your host machine and go to [duckdns.org](https://www.duckdns.org).
2. Log in (GitHub, Google, or Reddit account).
3. Choose a subdomain name (e.g. `mylab2026`) and click **add domain**.
4. Set the IP to your host machine's university IP (found in step 4a).
5. Note down your **token** (visible at the top of the DuckDNS page after login) and your full domain: `<yourname>.duckdns.org`.

Verify DNS propagation:

```bash
dig <yourname>.duckdns.org
```

**Checkpoint**: the `ANSWER SECTION` should show your university IP.

### 4c — Install certbot with the DuckDNS plugin

The `dns-duckdns` plugin is not in the Ubuntu repositories — install it in a virtualenv:

```bash
sudo apt install -y python3-venv
python3 -m venv ~/lab03/certbot-venv
~/lab03/certbot-venv/bin/pip install certbot certbot-dns-duckdns
```

Create the credentials file:

```bash
echo "dns_duckdns_token = <YOUR_TOKEN>" > ~/lab03/duckdns.ini
chmod 600 ~/lab03/duckdns.ini
```

### 4d — Obtain the certificate

```bash
sudo ~/lab03/certbot-venv/bin/certbot certonly \
  --authenticator dns-duckdns \
  --dns-duckdns-credentials ~/lab03/duckdns.ini \
  --dns-duckdns-propagation-seconds 60 \
  -d <yourname>.duckdns.org
```

certbot will:

1. Generate a key pair for your domain.
2. Ask Let's Encrypt for a challenge.
3. Automatically add a `_acme-challenge` TXT record to your DuckDNS domain.
4. Wait 60 seconds for DNS propagation.
5. Let's Encrypt verifies the TXT record and issues the certificate.
6. The certificate is saved to `/etc/letsencrypt/live/<yourname>.duckdns.org/`.

**Checkpoint**: certbot prints `Successfully received certificate`.

Copy the certificate files to the lab folder:

```bash
sudo mkdir -p ~/lab03/cert-le
sudo cp /etc/letsencrypt/live/<yourname>.duckdns.org/fullchain.pem ~/lab03/cert-le/
sudo cp /etc/letsencrypt/live/<yourname>.duckdns.org/privkey.pem  ~/lab03/cert-le/
sudo chown ubuntu:ubuntu ~/lab03/cert-le/*.pem
```

Inspect the certificate:

```bash
openssl x509 -in ~/lab03/cert-le/fullchain.pem -noout -text | head -30
```

**Checkpoint**: `Issuer` contains `Let's Encrypt`. The certificate is signed by a publicly trusted CA — not your lab CA.

### 4e — Configure NGINX with the Let's Encrypt certificate

Update the NGINX config to use the new certificate:

```bash
sudo tee /etc/nginx/sites-available/lab03-le > /dev/null << EOF
server {
    listen 444 ssl;
    server_name <yourname>.duckdns.org;

    ssl_certificate     /home/ubuntu/lab03/cert-le/fullchain.pem;
    ssl_certificate_key /home/ubuntu/lab03/cert-le/privkey.pem;

    root /var/www/lab03;
    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/lab03-le /etc/nginx/sites-enabled/lab03-le
sudo nginx -t && sudo systemctl reload nginx
```

> We use port 444 to avoid conflicting with the self-signed cert on 443.

### 4f — Connect from Alice without specifying a CA

> **Note**: this checkpoint requires inbound connectivity to your host machine. If you are working from home or behind a carrier-grade NAT (CGNAT), incoming connections will not reach Bob. Run this checkpoint from the university network, where machines have a direct public IP.

On Alice:

```bash
curl https://<yourname>.duckdns.org:444
```

**Checkpoint**: curl succeeds and prints `Hello from Bob over TLS!` — **without** `--cacert`. The OS already trusts Let's Encrypt.

Compare with Exercise 2: there you needed `--cacert ca.cert` because your self-signed CA was unknown. Here, Let's Encrypt is in the system trust store, so no extra configuration is needed on the client side.

**Question**: what is the practical difference between a self-signed certificate (ES01) and a Let's Encrypt certificate (ES04) from a security standpoint? Which one should you use in production?

### 4g — Verify the certificate chain

> **Note**: same as 4f — requires university network.

On Alice:

```bash
openssl s_client -connect <yourname>.duckdns.org:444 2>/dev/null | openssl x509 -noout -issuer -subject
```

You should see a chain from your domain up through Let's Encrypt intermediate CA to the ISRG Root X1 root CA.

---

## Troubleshooting

### nginx -t fails: "cannot load certificate"

Check that the paths in the NGINX config match the actual file locations:

```bash
ls -la ~/lab03/cert/
```

The NGINX process runs as `www-data` — make sure it can read the cert files:

```bash
sudo chmod 644 ~/lab03/cert/server.cert
sudo chmod 640 ~/lab03/cert/server.key
sudo chown root:www-data ~/lab03/cert/server.key
```

### curl: SSL certificate problem (ES02)

If you get `SSL certificate problem: unable to get local issuer certificate`, you did not pass `--cacert ca.cert` or the path is wrong. Remember that `ca.cert` must be transferred from Bob to Alice first.

### Python: ssl.SSLCertVerificationError (ES03)

The client cannot verify the server certificate. Check:

1. That `ca.cert` is the same CA that signed `server.cert`: run `openssl verify -CAfile ca.cert server.cert` on Bob — should print `OK`.
2. That `server_hostname` in `wrap_socket()` matches the CN or a SAN in the certificate (`bob.lab`).
3. That the `CA_CERT` environment variable points to the correct path if you are using it.

### es03_mitm crashes immediately (ES03e)

Darth's proxy connects to Bob at startup. If Bob's server is not running, the proxy crashes. Start in order: Bob first, then Darth, then Alice.

### Port 10443 already in use

```bash
sudo lsof -i :10443
```

Kill the process using that port, or change the port number in both server and client.

### Darth sees no traffic in Wireshark (ES03c)

Check that you replaced the switch with a hub in GNS3. With a switch, Darth only sees traffic addressed to Darth's MAC.

### curl fails on ES04 domain

First, check if you are behind a CGNAT. Run both commands on your host machine:

```bash
# macOS
ipconfig getifaddr en0

# Ubuntu/Linux
hostname -I | awk '{print $1}'

# IP visible from the internet (both)
curl -s https://api.ipify.org
```

If the two IPs are **different**, you are behind CGNAT — inbound connections cannot reach you. Use the university network instead.

If they are the **same**, check that port forwarding is active (`pfctl`) and that DuckDNS points to that IP.

---

## Open questions

1. In ES03, Alice verified Bob's identity using `ca.cert`. But Bob did not verify Alice's identity at all. What would be needed to make it mutual (mTLS)?
2. In Lab 02, the key `mysecretkey` had to be the same on both sides. In ES03, which files must be kept secret? Which can be shared publicly?
3. `openssl s_client` output shows a cipher suite like `TLS_AES_256_GCM_SHA384`. Which part of that is asymmetric? Which part is symmetric?
4. If you regenerate the server certificate (same CA, same CN, new key pair), what happens to existing clients that have a cached connection? What about clients that just have `ca.cert`?
5. Why does TLS use asymmetric crypto only for the handshake and then switch to symmetric? Why not use asymmetric for everything?
