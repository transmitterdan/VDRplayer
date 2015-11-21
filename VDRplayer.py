#	This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
	
import socket
import sys
import time

if len(sys.argv) < 4:
    print("USAGE:")
    print("[python] VDRServer1.py InputFile IP_Address Port# [Sleep time]")
    print("Sleep time is the delay in seconds between UDP messages sent.")
    print("Sleep time defaults to 0.1 seconds")
    sys.exit()

UDP_IP = sys.argv[2]
UDP_PORT = int(sys.argv[3])
filename = sys.argv[1]

if len(sys.argv) > 4:
    delay = float(sys.argv[4])
else:
    delay = 0.1

print(['UDP target IP:', UDP_IP])
print(['UDP target port:', str(UDP_PORT)])

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
f = open(filename, 'r')

while True :
    mess = f.readline()
    if len(mess) < 1:
        f.close()
        sys.exit()
#    print(mess)
    mess = mess.strip()
    sock.sendto(mess.encode("utf-8"),(UDP_IP, UDP_PORT))
    time.sleep(delay)

