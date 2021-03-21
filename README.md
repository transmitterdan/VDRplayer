# VDRplayer
Play VDR files over IP link.

Usage:

python3 VDRplayer.py FileName [--addr=IP_ADDR --port=PORT --sleep=N.N ["TCP"/"UDP"] --wait=NN]

  - Filename   Specifies name of a text file containing lines of characters terminated by newline.

  - IP_ADDR    Specifies the IP address in case the computer has more than one IP address. Clients should attempt to connect to this address.  Default is "localhost".

  - PORT       Specifies the integer port number to establish the link. This must match the port number expected by the client receiver. Default is 10110.

  - N.N        Specifies optional delay in seconds between each line sent to the client. If not specified then 0.1 (100mS)is the default.

  - TCP/UDP    Three character string specifying protocol to use. Default is "UDP".

  - NN         Time in seconds to wait for TCP connection from a client.  Default is 60.
  

VDRplayer is a Python script that will read a text file of lines. Each line is read and sent via UDP or TCP to the IP and port address provided on the command line. Any whitespace at the beginning or end of each line is stripped and \r\n is appended before sending over the link. This is useful for sending previously recorded Voyage Data Recorder files to an NMEA compatible chart plotter such as OpenCPN.

* **Example:**

python VDRplayer.py Hakefjord.txt 127.0.0.1 10110 0.05 TCP

Hakefjord.txt is a sample NMEA data file generously donated by Håkan on Cruisers Forum.

For UDP mode the IP address 127.0.0.1 is also known as localhost and used when sending to a client on the same machine. The IP address of any other machine on the network may be given.

For TCP mode the IP address is the address of the machine running VDRplayer. It may be localhost or 127.0.0.1 if the client is running on the same machine. If VDRplayer is running on its own machine then give the IP address of that machine that other clients can reach (e.g. 192.168.1.6 assuming that is the address of the machine running VDRplayer.py).

The port number 10110 is somewhat arbitrary but it is the "undocumented standard" for NMEA over IP and must match the client receiver port number. Any port number permitted by the local firewall will work. It is best not to use well known port numbers such as 80, 22, etc.

The time delay of 0.05 (50mS) is the delay between each line in the file.

This script has been tested on Windows and Ubuntu Linux (Wily) but it should work on nearly all host platforms with a modern (=>2.7) version of Python. Works with Python 3.4.

Download the current version of Python here: https://www.python.org/downloads/ or on Ubuntu: sudo apt-get install python3
