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

def udp():
    UDP_IP = sys.argv[2]
    UDP_PORT = int(sys.argv[3])
    filename = sys.argv[1]
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
                sys.exit()

	    #    print(mess)
            mess = mess.strip()
            mess = mess + u"\r\n"
            sock.sendto(mess.encode("utf-8"),(UDP_IP, UDP_PORT))
            time.sleep(delay)
        except KeyboardInterrupt:
            f.close()
            sock.close()
            break
        except Exception:
            f.close()
            sock.close()
            break

#   First pass at TCP connection. We are not sure whether to send packets
#   on the connection recommended by the client or to send to the specified
#   IP/port like in UDP. Both seem to work with OpenCPN but it seems more
#   "normal" tosend the data to the address and port provided by the client
#   so that's what we do.

def tcp():
    TCP_IP = sys.argv[2]
    TCP_PORT = int(sys.argv[3])
    filename = sys.argv[1]
    BUFFER_SIZE = 20
    print(['TCP target IP:', TCP_IP])
    print(['TCP target port:', str(TCP_PORT)])
    lsock = socket.socket(socket.AF_INET, # Internet
                            socket.SOCK_STREAM) # TCP
    lsock.bind((TCP_IP, TCP_PORT))
    lsock.listen(1)
    conn, addr = lsock.accept()
    print(['Connection address:', addr]);
    f = open(filename, 'r')
    print("Type Ctrl-C to exit...")
    while True:
        try:
            mess = f.readline()
            if len(mess) < 1:
                f.close()
                conn.close()
                lsock.close()
                sys.exit()

    #        print(mess)
            mess = mess.strip()
            mess = mess + u"\r\n"
            conn.send(mess.encode("utf-8"))
            time.sleep(delay)
        except KeyboardInterrupt:
            f.close()
            conn.close()
            lsock.close()
            break
        except Exception:
            f.close()
            conn.close()
            lsock.close()
            break

if len(sys.argv) < 5:
    print("USAGE:")
    print("[python] VDRServer1.py InputFile IP_Address Port# [Sleep time [TCP]]")
    print("Sleep time is the delay in seconds between UDP messages sent.")
    print("Sleep time defaults to 0.1 seconds")
    print("If three letter string after sleep time is TCP then TCP/IP packets are sent")
    print("else UDP packets are sent.")
    sys.exit()


if len(sys.argv) > 4:
    delay = float(sys.argv[4])
else:
    delay = 0.1

if len(sys.argv) > 5:
    mode = sys.argv[5]
else:
    mode = "UDP"

if mode.upper() == "UDP":
    udp()

if mode.upper() == "TCP":
    tcp()

sys.exit()
