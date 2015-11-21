# VDRplayer
Play VDR files through UDP

VDRplayer is a Python script that will read a text file of lines. Each line is read and sent via UDP to the IP and port address provided on the command line. Any whitespace at the beginning or end of each line is stripped before sending over the UDP link.

Usage:

python VDRplayer.py Hakefjord.txt 127.0.0.1 2947

The IP address 127.0.0.1 is also known as localhost.
The port number 2947 is somewhat arbitrary but it must match the UDP receiver port number.

This script has been tested on Windows and Ubuntu Linux (Wily) but it should work on nearly all host platforms with a modern (=>2.7) version of Python.
