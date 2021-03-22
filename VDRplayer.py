#!/usr/bin/env python3
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

assert sys.version_info >= (3, 3), "Must run in Python 3.3"

import selectors
import types
import time
import string
import getopt


# Command line options
options, remainder = getopt.gnu_getopt(sys.argv[1:], 'd:ho:p:rs:ut',
 ['dest=', 'help', 'host=', 'port=', 'repeat=', 'sleep=', 'UDP','TCP'])

# Set default options
mode = 'UDP'
dest = 'localhost'
host = socket.gethostname()
IPport = None
td = 0.1
Repeat = 1

def openFile(fName):
    if fName:
        f = open(fName,'r')
    else:
        f = sys.stdin
    # End if
    if not f:
        raise FileExistsError()
    # End if
    return f
# End openFile()

def getMessage(f, Delay):
    time.sleep(Delay)
    if f:
        mess = f.readline()
    else:
        print("End of file reached...")
        return False
    # End if
    if len(mess) == 0:
        raise EOFError()
    # End if
    mess = mess.strip()
    mess = mess + u"\r\n"
    return(mess.encode("utf-8"))
# End getMessage()

def udp(Dest, Port, fName, Delay, Repeat):
    if Port == None:
        Port = 10110
    # End if
    f = openFile(fName)
    print(['UDP target IP:', Dest])
    print(['UDP target port:', str(Port)])
    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
    # Allow UDP broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    print("Type Ctrl-C to exit...")
    while True:
        try:
            while True :
                sock.sendto(getMessage(f, Delay),(Dest, Port))
            # End while
        except KeyboardInterrupt:
            f.close()
            sock.close()
            return True
        # End except
        except EOFError:
            Repeat -= 1
            if Repeat > 0:
                f.seek(0)
                print("Repeating file...")
                continue
            f.close()
            sock.close()
            return True
        # End except
        except Exception:
            f.close()
            sock.close()
            raise
# End udp()

## Now we create the TCP version.
# It's more complex because we want to
# accept multiple client connections
# simultaneously.

sel = selectors.DefaultSelector()

def accept_wrapper(sock):
    conn, addr = sock.accept()
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    print("Accepted connection from client: ", data.addr)
# End accept_wrapper()

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if not recv_data:
            print("Closing connection to client:", data.addr)
            sel.unregister(sock)
            sock.close()
            return
        # End if
    # End if
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]
        # End if
    # End if
# End service_connection()

def tcp(Host, Port, fName, Delay, Repeat):
    if Port == None:
        Port = 2947
    # End if
    f = openFile(fName)
    server_address = (Host, Port)
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind(server_address)
    lsock.listen()
    listening = lsock.getsockname()
    print("Server at address: " + str(listening[0]) + " is listening on port: " + str(listening[1]))
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)
    while True:
        try:
            events = sel.select()
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    mess = getMessage(f, Delay)
                    if mess:
                        key.data.outb += mess
                        try:
                            service_connection(key, mask)
                        except ConnectionAbortedError:
                            print("ConnectionAbortedError: Attempting to close connection to client:", key.data.addr)
                            sock = key.fileobj
                            sel.unregister(sock)
                            sock.close()
                        # End try
                    # End if
                # End if
            # End for
        except EOFError:
            Repeat -= 1
            if Repeat > 0:
                f.seek(0)
                print("Repeating file...")
                continue
            f.close()
            lsock.close()
            return True
        # End except
        except KeyboardInterrupt:
            lsock.close()
            if f:
                f.close()
            # End if
            return True
        except:
            lsock.close()
            if f:
                f.close()
            # End if
            raise
        # End try
    # End while
# End tcp()

def usage():
    print("USAGE:")
    print("[python3] VDRplayer.py [--port=Port#] [--sleep=Sleep time] [--TCP --host=localhost | --UDP --dest=UDP_IP_Address] InputFile")
    print("")
    print("Commandline options:")
    print("")
    print("-d, --dest=IP_Address  UDP destination IP address.")
    print("                       Default will resolve to 'localhost'")
    print("")
    print("-h, --help             print this message.")
    print("")
    print("-o, --host=IP_Address  TCP server IP address.")
    print("                       This must resolve to a valid IP address on this computer.")
    print("")
    print("-p, --port=#           optional communication port number.")
    print("                       Any valid port is accepted.")
    print("")
    print("-r, --repeat=#         optional number of times to reread input file.")
    print("                       Any valid port is accepted.")
    print("")
    print("-s, --sleep=#.#        optional seconds delay between packets.")
    print("                       default is 0.1 seconds.")
    print("")
    print("-t, --TCP              create TCP server on primary IP address.")
    print("                       Default will resolve to local machine name.")
    print("                       Specify IP address using --host option to override default.")
    print("")
    print("-u, --UDP              create connectionless UDP link.")
    print("                       UDP is the default if no connection type specified.")
    print("                       Specify destination IP address using --dest option.")
    print("")
    print("InputFile              Name of file containing NMEA message strings.")
    print("                       If no FILE is given then default is to read")
    print("                       input text from STDIN.")
    return
# End usage()

# Pick up all commandline options
try:
    for opt, arg in options:
        if opt.lower() in ('-d', '--dest'):
            dest = arg
        elif opt.lower() in ('-p', '--port'):
            IPport = int(arg)
        elif opt.lower() in ('-s', '--sleep'):
            td = float(arg)
        elif opt.lower() in ('-u', '--udp'):
            mode = 'UDP'
        elif opt.lower() in ('-t', '--tcp'):
            mode = 'TCP'
        elif opt in ('-o', '--host'):
            host = arg
        elif opt in ('-r', '--repeat'):
            if len(arg) > 0:
                Repeat = int(arg)
        elif opt.lower() in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            print("Unknown option: ", opt)
            usage()
            sys.exit(2)
        # End if
    # End for
except getopt.GetoptError as msg:
    print(msg)
    sys.exit(2)
# End try

# Main program
rCode = False

if mode.upper() == "UDP":
    rCode = udp(dest, IPport, remainder[0], td, Repeat)
elif mode.upper() == "TCP":
    Host = socket.gethostbyname(host)
    rCode = tcp(Host, IPport, remainder[0], td, Repeat)
else:
    print(['Unknown communication link type', mode])
# End if
if rCode == True:
    print("Exiting cleanly.")
    sys.exit(0)
else:
    print("Something went wrong, exiting.")
    sys.exit(1)
# End if
