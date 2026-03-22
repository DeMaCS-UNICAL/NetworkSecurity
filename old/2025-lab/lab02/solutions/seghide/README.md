## **ES 03: Smutt - Steganography**

In this exercise, you will create a Python script, `smutt.py`, which utilizes steganography:

```shell
# Inject data into an image file
$ steghide embed -cf image.jpg -ef text -sf image_text.jpg

# Extract data from an image file
$ steghide extract -sf image_text.jpg
```

To make **Mutt** work with Gmail, you need an **app password** from:

[Google App Passwords](https://myaccount.google.com/apppasswords)

Example of a `~/.muttrc` configuration file:

```conf
# Example of ~/.muttrc file
set imap_user = "USERNAME@gmail.com"
set imap_pass = "PASSWORD"
set folder = "imaps://imap.gmail.com/"
set spoolfile = "+INBOX"
set postponed = "+[Gmail]/Drafts"
set record = "+[Gmail]/Sent Mail"
set header_cache = "~/.mutt/cache/headers"
set message_cachedir = "~/.mutt/cache/bodies"
set certificate_file = "~/.mutt/certificates"
set smtp_url = "smtps://USERNAME@gmail.com@smtp.gmail.com:465/"
set smtp_pass = "PASSWORD"
set from = "USERNAME@gmail.com"
set realname = "NAME SURNAME"
set editor = "nano"
```

Example of sending an email with an attachment (**working example!**):

```bash
$ mutt -s "beautiful image" USERNAME@gmail.com -a image_text.jpg
```

