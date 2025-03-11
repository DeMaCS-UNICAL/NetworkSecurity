"""
Start server
$ python cryptocat.py --mode server --key mysecretkey localhost 7890

Start client
$ python cryptocat.py --mode client --key mysecretkey localhost 7890
"""


import subprocess
import argparse
import threading
parser = argparse.ArgumentParser()

parser.add_argument("host", help="In server mode is listen ip, in client mode is host to send data")
parser.add_argument("port", help="In server mode is listen port, in client mode is port to send data")
parser.add_argument("--mode", help="server or client", required=True )
parser.add_argument("--key", help="shared secret beetwen parties", required=True)

args = parser.parse_args()
mode = args.mode
host = args.host 
port = args.port
key = args.key

print("Start with mode: %s, host: %s, port: %s, key: %s" % (mode, host, port, key))

def read_output(proc):
    while True:
        data = proc.stdout.read1(1024)
        if not data:
            break
        encoedData = data.decode().strip()
        decodecProcessResult = subprocess.run(["echo \""+ encoedData +"\" | openssl enc -aes-256-cbc -base64 -pbkdf2 -pass pass:"+ key +" -d"], stdout=subprocess.PIPE,  shell=True)
        print(decodecProcessResult.stdout.decode(), end='', flush=True)

if mode == "server":
    netcatcmd = ["netcat","-lp", port, host]
elif mode == "client":
    netcatcmd = ["netcat", host, port]

proc = subprocess.Popen(netcatcmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
read_thread = threading.Thread(target=read_output, args=(proc,))
read_thread.start()

while True:
    user_input = input()
    inputString = user_input.strip()
    encodedProcessResult = subprocess.run(["echo \""+ inputString +"\" | openssl enc -aes-256-cbc -base64 -pbkdf2 -pass pass:"+ key +" -e"], stdout=subprocess.PIPE, shell=True)
    proc.stdin.write(f"{encodedProcessResult.stdout.decode()}\n".encode())
    proc.stdin.flush()

print("That's all, folks!")