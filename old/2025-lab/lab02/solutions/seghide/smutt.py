"""
$ python smutt.py --ef efilename --cf cfilename --sf sfilename address
"""

import subprocess
import argparse
import threading
parser = argparse.ArgumentParser()

parser.add_argument("--ef", required=True)
parser.add_argument("--cf", required=True)
parser.add_argument("--sf", required=True)
parser.add_argument("address", help="Receiver Address") 

args = parser.parse_args()
eFilename = args.ef
cFilename = args.cf
sFilename = args.sf
address = args.address

print("Start with eFilename: %s, cFilename: %s, sFilename: %s, address: %s" % (eFilename, cFilename, sFilename, address))

steghide_command = f'steghide embed -cf {cFilename} -ef {eFilename} -sf {sFilename} -p paola'
mutt_command = f'mutt -s "guarda che panorama!" {address} -a {cFilename} '

steghideProc = subprocess.run(steghide_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
muttProc = subprocess.run(mutt_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

print("That's all, folks!")

