# Session 01 — GNS3 Installation (macOS)

**OS**: macOS (Apple Silicon — M1/M2/M3/M4/M5)

> This guide covers **only the macOS-specific installation of GNS3**.
> Once GNS3 is running, follow the Ubuntu guide (`01_gns3_setup.md`)
> from **Step 3** onward for everything else: first launch, templates, topology, network config, and verification.

**Credentials summary** (keep handy):

| Machine        | Username | Password          |
| -------------- | -------- | ----------------- |
| Alice / Bob    | `ubuntu` | `ubuntu`          |
| Darth          | `pi`     | `raspberry`       |
| Cisco R1 / SW1 | —        | no login required |

## Step 1 — Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Add Homebrew to your PATH (shown at the end of the install output):

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

---

## Step 2 — Install dependencies and GNS3

```bash
brew install qemu cmake libpcap libelf pkg-config pipx
brew install --cask gns3
```

`brew install --cask gns3` installs both the GUI (`.app`) and a bundled server. The bundled server has Python dependency conflicts on macOS — **do not use it**. The next step installs the correct server.

---

## Step 3 — Install GNS3 server via pipx

```bash
pipx install gns3-server
```

Verify:

```bash
~/.local/bin/gns3server --version
```

> Always launch the server with `~/.local/bin/gns3server`, not the one bundled in `/Applications/GNS3.app`.

---

## Step 4 — Build and install ubridge from source

`ubridge` is not available in Homebrew on macOS.

First, make sure the Xcode Command Line Tools are installed (required for `git` and `make`):

```bash
xcode-select --install
```

If already installed you will see an error — ignore it and continue.

```bash
cd /opt
sudo git clone https://github.com/GNS3/ubridge.git
sudo chown -R $(whoami) ubridge
cd ubridge
make
sudo make install
which ubridge   # should print /usr/local/bin/ubridge
```

---

## Step 5 — Build and install dynamips from source

```bash
cd /opt
sudo git clone https://github.com/GNS3/dynamips.git
sudo chown -R $(whoami) dynamips
cd dynamips
mkdir build && cd build
cmake .. -DDYNAMIPS_CODE=stable
make
sudo make install
which dynamips  # should print /usr/local/bin/dynamips
```

---

## Step 6 — Fix macOS TCP socket bug in gns3-server

Without this fix, console connections to devices will fail. The issue is that macOS uses `TCP_KEEPALIVE` where Linux uses `TCP_KEEPIDLE`.

```bash
TELNET_FILE=$(find ~/.local/pipx/venvs/gns3-server -name 'telnet_server.py')
sed -i '' 's/TCP_KEEPIDLE/TCP_KEEPALIVE/g' "$TELNET_FILE"
grep -n 'TCP_KEEP' "$TELNET_FILE"   # verify the fix
```

> **Important**: this fix must be reapplied every time you upgrade gns3-server (`pipx upgrade gns3-server`), because the upgrade replaces the file.

---

## Step 7 — Start the GNS3 server

Open a dedicated terminal window and run:

```bash
~/.local/bin/gns3server
```

Wait until you see this line in the output before launching the GUI:

```
INFO  Starting server on 0.0.0.0:3080
```

Leave this terminal open. Then launch the GUI:

```bash
open /Applications/GNS3.app
```

In the Setup Wizard:

**1. Select "Run the topologies on my local computer":**

![Setup Wizard — server type](img/gns-setup-00.png)

**2. Local server config — set path to `~/.local/bin/gns3server`, host `localhost`, port `3080`:**

> The screenshot shows `/usr/bin/gns3server` (Ubuntu path) — on macOS use `~/.local/bin/gns3server` instead.

![Setup Wizard — local server config](img/gns-setup-01.png)

**3. Connection successful:**

![Setup Wizard — connection OK](img/gns-setup-02.png)

**4. Summary — verify settings:**

![Setup Wizard — summary](img/gns-setup-03.png)

**5. GNS3 main window:**

![GNS3 main window](img/gns-setup-04.png)

**6. Configure VNC viewer:**

Go to **Edit → Preferences → General → Console applications** and set:

- **VNC viewer**: `vncviewer %h:%p`

> The macOS built-in Screen Sharing viewer does not work correctly with GNS3. Install TigerVNC instead:
>
> ```bash
> brew install --cask tigervnc-viewer
> ```
>
> The binary is `vncviewer` — same command as on Linux.

---

## Step 8 — Configure NAT (internet access for the lab)

macOS does not have `virbr0` or `libvirt`. NAT is set up manually with a virtual bridge and `pfctl`.

> These settings are lost on reboot — rerun this block every time before opening GNS3.

**1. Create a virtual bridge** (any number ≥ 2 — bridge0 is reserved by the system):

```bash
sudo ifconfig bridge9 create
sudo ifconfig bridge9 192.168.122.1 netmask 255.255.255.0 up
```

**2. Create a virtual ethernet pair and attach it to the bridge:**

```bash
sudo ifconfig feth0 create
sudo ifconfig feth1 create
sudo ifconfig feth0 peer feth1
sudo ifconfig feth0 up
sudo ifconfig feth1 up
sudo ifconfig bridge9 addm feth0
sudo ifconfig bridge9 up
```

**3. Enable IP forwarding:**

```bash
sudo sysctl -w net.inet.ip.forwarding=1
```

**4. Find your internet interface:**

```bash
route get default | grep interface
# Example output:  interface: en0
```

**5. Set up NAT with pf** (replace `en0` with your interface):

```bash
echo "nat on en0 from 192.168.122.0/24 to any -> (en0)" | sudo pfctl -N -f -
sudo pfctl -e
```

> These are two separate commands: the first loads the NAT rule, the second enables pf. If pf is already enabled the second command will print an error — ignore it.

In GNS3, when adding the Cloud node, select `bridge9` (not `virbr0`) as the interface.

> **Note**: a convenience script that runs all of Step 8 in one command will be published on the course GitHub repository at the end of the session.

---

## Continue with the Ubuntu guide

From this point, **follow `01_gns3_setup.md` from Step 3** — first launch wizard, disk images, device templates, topology, VM configuration, and verification are identical.

The only difference: in the Cloud node configuration, select `bridge9` instead of `virbr0`.

---

## Troubleshooting (macOS-specific)

### Console connection to devices fails (blank terminal)

The TCP_KEEPALIVE fix (Step 6) was not applied, or gns3-server was already running when you applied it. Stop the server, reapply, restart.

### bridge9 / feth0 disappear after reboot

Expected — macOS does not persist virtual interfaces. Rerun Step 8 before every session.

### GNS3 GUI cannot connect to server

Make sure `~/.local/bin/gns3server` is running in a separate terminal before launching the GUI.

### dynamips or ubridge not found by GNS3

Go to **Edit → Preferences → Dynamips** and **Edit → Preferences → General** and set the paths to `/usr/local/bin/dynamips` and `/usr/local/bin/ubridge`.

### QEMU VMs do not start

```bash
which qemu-system-x86_64   # must return a path
brew reinstall qemu         # if missing
```
