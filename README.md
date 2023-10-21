# VDRplayer
Play Voyage Data Recorder files over IP link.

USAGE:
```
[python3] VDRplayer.py [--port=Port#] [--sleep=Sleep time] [--TCP --host=localhost | --UDP --dest=UDP_IP_Address] InputFile

Commandline options:

  -h | --help - print this message.

  -d IP_Address | --dest=IP_Address - UDP destination IP address.  Overrides primary address.
  -o IP_Address | --host=IP_Address - TCP server IP address. This must resolve to a valid IP address on this computer.
      NOTE: The dest and host options are mutually exclusive

  -p # | --port=# - optional communication port number. Any valid port is accepted.

  -r # | --repeat=# - optional number of times to reread input file. Any valid port is accepted.

  -s #.# | --sleep=#.# - optional seconds delay between packets, when there is no timestamp in NMEA packets. Default is 0.1 seconds.

  -f #.# | --fast=#.# - optional speed acceleration factor if NMEAv4. Default factor is 1.0.

  -t, --TCP - create TCP server on primary IP address.  Specify any IP address using --host option to override default.

  -u, --UDP - create connectionless UDP link. UDP is the default if no connection type specified. Specify destination IP address using --dest option. if no --dest given then IP address will resolve to 'localhost'.
      NOTE: The TCP and UDP options are mutually exclusive.

  InputFile - Name of file containing NMEA message strings. If no FILE is given then default is to read input text from STDIN.
```

VDRplayer is a Python script that will stream a file containing NMEA data such as recorded by an NMEA Voyage Data Recorder. Each line is read and sent via UDP or TCP to the IP and port address provided on the command line. Any whitespace at the beginning or end of each line is stripped and \r\n is appended before sending over the link. This is useful for sending previously recorded Voyage Data Recorder files to an NMEA compatible chart plotter such as OpenCPN.  OpenCPN has a VDR plugin that will record any voyage for later playback.

* **Example 1:**

```
user@Linux:~/VDRplayer$ ./VDRplayer.py --sleep=0.07 --dest=192.168.0.255 --port=10110 Hakefjord.txt
Playing file 'Hakefjord.txt', Type Ctrl-C to exit...
  UDP target IP: 192.168.0.255
UDP target port: 10110
Inserting 70.00 mS delay between each message.
```

* **Example 2:**

```
user@Linux:~/VDRplayer$ ./VDRplayer.py --sleep=0.07 --dest=192.168.0.255 --port=10110 Hakefjord.txt
Playing file 'Hakefjord.txt', Type Ctrl-C to exit...
Server at address: 192.168.0.123 is listening on port: 2947
Accepted connection from client:  ('192.168.0.123', 59380)
```

Hakefjord.txt is a sample NMEA data file generously donated by Håkan on Cruisers Forum.

For UDP mode the dest IP address 127.0.0.1 is also known as localhost and used when sending to a client on the same machine. The IP address of any other machine on the network may be given.

For TCP mode the host IP address is the address of the machine running VDRplayer. It may be localhost or 127.0.0.1 if the client is running on the same machine. If VDRplayer is running on its own machine then supply an IP address on that machine that other clients can reach (e.g. 192.168.1.6 assuming that is the address of the machine running VDRplayer.py). The program will automatically select a host IP address if none is given.

Any port number permitted by the local firewall will work. It is best not to use well known port numbers such as 80, 22, etc.

The sleep delay is the delay in seconds between each line in the file.

This script has been tested on Windows and Ubuntu Linux (bionic) but it should work on nearly all host platforms with a modern (=>3.5) version of Python.

Download the current version of Python here: https://www.python.org/downloads/ or on Ubuntu: sudo apt-get install python3

There are other NMEA data files available on the internet.  The excellent NavMonPC program by Paul Elliot and Dirk Lison uses the same file format.  They provide example data files that work with VDRplayer here: http://navmonpc.com/downloads.html

If you find other online sources of sample NMEA data files please submit a PR to this README.md.
