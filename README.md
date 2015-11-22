# VDRplayer
Play VDR files through UDP

Usage:

[python[3]] VDRplayer.py FileName IP_ADDR PORT [Delay ["TCP"/"UDP"]]

  Filename      Specifies name of a text file containing possibly lines of characters 
                terminated by newline.
  
  IP_ADDR       Specifies the IP address of a client computer (possible same address 
                as the player)
  
  PORT          Specifies the integer port number to establish the link. This must 
                match the port number expected by the client receiver.
				
  Delay         Specifies optional delay in seconds between each line sent to the client.
                If not specified then 100mS is the default.
				
  TCP/UDP       Three character string specifying protocol to use.
  

VDRplayer is a Python script that will read a text file of lines. Each line is read and 
sent via UDP or TCP to the IP and port address provided on the command line. Any 
whitespace at the beginning or end of each line is stripped and \r\n is appended before 
sending over the link.

Example:

python VDRplayer.py Hakefjord.txt 127.0.0.1 10110 0.05 TCP


The IP address 127.0.0.1 is also known as localhost and used when sending to a client 
on the same maching. The IP address of any other machine on the network may also be given.

The port number 10110 is somewhat arbitrary but it is the "undocuemented standard" for 
NMEA and must match the client receiver port number.

The time delay of 0.05 (50mS) is the delay between each line in the file.

This script has been tested on Windows and Ubuntu Linux (Wily) but it should work on 
nearly all host platforms with a modern (=>2.7) version of Python. Works with Python 3.4.

Download the current version of Python here: https://www.python.org/downloads/ or 
sudo apt-get install python[3] on Ubuntu
