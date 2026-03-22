## **ES 01: CryptoCat - Encrypted Communication**

You need to create a Python script, `cryptocat.py`, that adds a layer of encryption to Netcat communication, which, by default, occurs in plaintext.

First, establish a Netcat connection:

```shell
# Server
netcat -lp 9999

# Client
netcat localhost 9999
```

Perform some message exchanges while monitoring traffic with Wireshark to see if you can read the conversation.

Next, test the encrypted version using your newly created script:

```shell
# Server
python cryptocat.py -m server -k <MYKEY> localhost 9999

# Client
python cryptocat.py -m client -K <MYKEY> localhost 9999
```

Try exchanging messages again and observe whether your ability to sniff the traffic changes!

```shell
$ echo "ciao" | openssl enc -aes-256-cbc -base64 -pbkdf2 -pass pass:mysecretkey -e
$ echo "U2FsdGVkX19WB/7sv22GvOlwB2EsvBBW6oCLt/mrVzY=" | openssl enc -aes-256-cbc -base64 -pbkdf2 -pass pass:mysecretkey -d
```
