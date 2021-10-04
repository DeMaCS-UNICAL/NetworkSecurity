import os, sys, argparse

parser = argparse.ArgumentParser(description='smutt.py')
parser.add_argument('-cf', '--source_image', type=str, help='input image')
parser.add_argument('-ef', '--data', type=str, help='data to encrypt')
parser.add_argument('-sf', '--output_data', type=str, default='output.jpeg', help='image with crypted data')
parser.add_argument('address', type=str, help='Receiver Address')

args = parser.parse_args()

if not args.source_image or not args.data or not args.address:
    print('Error!')
    parser.print_usage()
    sys.exit(0)./

steghide_command = 'steghide embed'
output = '-sf %s' % args.output_data

os.system('%s -cf %s -ef %s %s' % (steghide_command, args.source_image, args.data, output))

## SEND EMAIL ##
os.system('echo Hi, checkout this new image!| mutt -s New Image -a %s -- %s' % (args.output_data, args.address))
