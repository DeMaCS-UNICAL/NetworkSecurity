import os, sys, argparse

parser = argparse.ArgumentParser(description='Cryptocat.py')
parser.add_argument('-a', '--algorithm', type=str, default='aes256', help='encryption/decryption algorithm')
parser.add_argument('-k', '--key', type=str, default='key', help='encryption/decryption key')
parser.add_argument('-l', '--listen', action='store_true', help='Server mode')
parser.add_argument('-p', '--plain_text', action='store_true', help='Select to disable cryptography layer')
parser.add_argument('-c', '--ciphers', action='store_true', help='Show allowed cipher list')
parser.add_argument('-host', '--hostname', type=str, help='Client ip address')
parser.add_argument('-port', '--port', type=str, default='9999', help='Port')

args = parser.parse_args()

if args.ciphers:
    os.system('openssl enc --ciphers')
    exit(0)

if args.listen:
    print('----SERVER MODE----')
    nc_command = 'nc -l %s ' % args.port
    crypto = 'openssl enc -%s -d -k %s -base64' % (args.algorithm, args.key)

    if args.plain_text:
        os.system(nc_command)
    else:
        os.system('%s | %s' % (nc_command, crypto))
else:
    print('----CLIENT MODE----')
    print('Write your message, type q to stop the input')
    f = open('input.txt', 'w')
    for line in sys.stdin:
        if 'q' == line.rstrip():
            break
        f.write(line)

    f.close()
    ip_address = args.hostname if args.hostname else '127.0.0.1'
    nc_command = 'nc %s %s -N' % (ip_address, args.port)
    crypto = 'openssl enc -%s -e -k %s -base64 -in input.txt' % (args.algorithm, args.key)
    if args.plain_text:
        os.system('%s < input.txt' % nc_command)
    else:
        os.system('%s | %s' % (crypto, nc_command))
    os.system('rm -f input.txt')
