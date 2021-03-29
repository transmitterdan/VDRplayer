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

import sys

assert sys.version_info >= (3, 3), "Must run in Python 3.3"

import socket
import selectors
import types
import time
import string
import getopt

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

def getNextMessage(f, Delay):
    if Delay > 0:
        time.sleep(Delay)
    if f:
        mess = f.readline()
    else:
        print("End of file reached...")
        return False
    # End if
    if len(mess) == 0:
        return False
    # End if
    mess = mess.strip()
    mess = mess + u"\r\n"
    return(mess.encode("utf-8"))
# End getNextMessage()

def udp(Dest, Port, fName, Delay, Repeat):
    f = openFile(fName)
    print("  UDP target IP: " + Dest)
    print("UDP target port: " + str(Port))
    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
    # Allow UDP broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    print("Type Ctrl-C to exit...")
    try:
        while True :
            nextMessage = getNextMessage(f, Delay)
            if not nextMessage:
                Repeat -= 1
                if Repeat > 0:
                    f.seek(0)
                    print("Repeating file...")
                    continue
                return True
            # End if
            sock.sendto(nextMessage,(Dest, Port))
        # End while
    except KeyboardInterrupt:
        print("KeyboardInterrupt.")
        return True
    # End except
    finally:
        sock.close()
        if f:
            f.close()
        # End if
    # End while
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
        print(str(len(recv_data)) + " characters received...")
        if not recv_data:
            print("Closing connection to client:", sock)
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
    clients = []
    Server = False
    server_address = (Host, Port)
    Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Server.bind(server_address)
    Server.listen(1)
    listening = Server.getsockname()
    print("Server at address: " + str(listening[0]) + " is listening on port: " + str(listening[1]))
    Server.setblocking(False)
    sel.register(Server, selectors.EVENT_READ, data=None)
    try:
        f = openFile(fName)
        while True:
            mess = getNextMessage(f, Delay)
            if not mess:
                Repeat -= 1
                if Repeat > 0:
                    f.seek(0)
                    print("Repeating file...")
                    continue
                else:
                    return True
                # End if
            # End if
            events = sel.select()
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                    clients.append(key.fileobj)
                else:
                    try:
                        key.data.outb += mess
                        service_connection(key, mask)
                    except ConnectionError as CE:
                        print(CE)
                        print("ConnectionError: Attempting to close connection to client:", key.data.addr)
                        sock = key.fileobj
                        clients.remove(sock)
                        sel.unregister(sock)
                        sock.close()
                    # End try
                # End if
            # End for
        # End while
    # End try
    except KeyboardInterrupt:
        print("KeyboardInterrupt...")
        return True

    except:
        print("Exception...")
        # Kill off the listening socket
        # The server sockets will die eventually
        for Client in clients:
            Client.close()
        Server.close()
        if Server:
            Server.close()
        if f:
            f.close()
        # End if
        raise

    finally:
        for Client in clients:
            Client.close()
        Server.close()
        if f:
            f.close()
        # End if
    # End try
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

# Command line options spec
options, remainder = getopt.gnu_getopt(sys.argv[1:], 'd:ho:p:rs:ut',
 ['dest=', 'help', 'host=', 'port=', 'repeat=', 'sleep=', 'UDP','TCP'])

# Set default options
mode = 'UDP'
dest = None
host = None
port = None
td = 0.1
Repeat = 1
rCode = False

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
if mode.upper() == "UDP":
    if dest == None:
        dest = socket.gethostbyname(socket.gethostname())
    if port == None:
        port = 10110
    rCode = udp(dest, IPport, remainder[0], td, Repeat)
elif mode.upper() == "TCP":
    if host == None:
        host = socket.gethostbyname(socket.gethostname())
    if port == None:
        port = 2947
    Host = socket.gethostbyname(host)
    rCode = tcp(Host, IPport, remainder[0], td, Repeat)
else:
    usage()
# End if
if rCode == True:
    print("Exiting cleanly.")
    sys.exit(0)
else:
    print("Something went wrong, exiting.")
    sys.exit(1)
# End if
