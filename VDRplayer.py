#!/usr/bin/env python
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket
import sys
import time

tdDefault = 0.1     # Default time between sent messages
tcpTimeout = 5.0    # Timeout for inactive TCP socket
tcpConnectTimeout = 60.0	# Wait 60 seconds for a connection then exit

def udp(UDP_IP, UDP_PORT, filename, delay):
    print(['UDP target IP:', UDP_IP])
    print(['UDP target port:', str(UDP_PORT)])
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
    f = open(filename, 'r')
    print("Type Ctrl-C to exit...")
    while True :
        try:
            mess = f.readline()
            if len(mess) < 1:
                f.close()
                sock.close()
                return True

	    #    print(mess)
            mess = mess.strip()
            mess = mess + u"\r\n"
            sock.sendto(mess.encode("utf-8"),(UDP_IP, UDP_PORT))
            time.sleep(delay)
        except KeyboardInterrupt:
            f.close()
            sock.close()
            return True
        except Exception as msg:
            print(msg)
            f.close()
            sock.close()
            return False

def tcp(TCP_IP, TCP_PORT, filename, delay):
    if TCP_IP == None:
        TCP_IP = socket.gethostname()

    server_address = (TCP_IP, TCP_PORT)

#    print(['TCP target IP:%s:%d', server_address])
#    print(['TCP target port:', str(TCP_PORT)])
    lsock = socket.socket(socket.AF_INET, # Internet
                          socket.SOCK_STREAM) # TCP
    lsock.settimeout(tcpConnectTimeout)
    try:
        lsock.bind(server_address)
        lsock.listen(1)
        print(["Server is waiting up to " + repr(tcpConnectTimeout) + "S for a connection at:", server_address]);
        conn, addr = lsock.accept()
    except socket.error as msg:
        print(msg)
        lsock.close()
        return False

    print(['Connecting to:', addr]);
    f = open(filename, 'r')
    print("Type Ctrl-C to exit...")
    while True:
        try:
            mess = f.readline()
            if len(mess) < 1:
                f.close()
                conn.close()
                lsock.close()
                return True

    #        print(mess)
            mess = mess.strip()
            mess = mess + u"\r\n"
            conn.send(mess.encode("utf-8"))
            time.sleep(delay)
        except KeyboardInterrupt:
            f.close()
            conn.close()
            lsock.close()
            return True
        except Exception as msg:
            print(msg)
            f.close()
            conn.close()
            lsock.close()
            return False

if len(sys.argv) < 5:
    print("USAGE:")
    print("[python] VDRplayer.py InputFile IP_Address Port# [Sleep time [TCP]]")
    print("Sleep time is the delay in seconds between UDP messages sent.")
    print("Sleep time defaults to 0.1 seconds")
    print("If three letter string after sleep time is TCP then TCP/IP packets are sent")
    print("else UDP packets are sent.")
    sys.exit()

if len(sys.argv) > 4:
    td = float(sys.argv[4])
else:
    td = tdDefault        # default time between messages

if len(sys.argv) > 5:
    mode = sys.argv[5]
else:
    mode = "UDP"

rCode = False

if mode.upper() == "UDP":
    rCode = udp(sys.argv[2], int(sys.argv[3]), sys.argv[1], td)

if mode.upper() == "TCP":
    rCode = tcp(sys.argv[2], int(sys.argv[3]),sys.argv[1], td)

if rCode == True:
    print("Exiting cleanly.")
else:
    print("Something went wrong, exiting.")

sys.exit()
