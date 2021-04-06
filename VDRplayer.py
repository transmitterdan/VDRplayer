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

assert sys.version_info >= (3, 5), "Must run in Python version 3.5 or above"

import socket
import selectors
import types
import time
import string
import getopt

class percentComplete:

    def __init__(self, tInc):
        self.oldTime = time.perf_counter()
        self.tInc = tInc

    def printPercent(self, percent):
        newTime = time.perf_counter()
        if (newTime - self.oldTime) > self.tInc:
            print(" %3.1f percent complete...." % round(percent, 1), end='\r')
            self.oldTime = newTime

def file_len(f):
    for i, l in enumerate(f):
        pass
    f.seek(0)
    return i + 1

def openFile(fName):
    Len = float('inf')
    if fName:
        try:
            f = open(fName,'r')
            print("Playing file '%s', Type Ctrl-C to exit..." % fName)
        except FileNotFoundError:
            print("File '%s' not found, exiting." % fName)
            sys.exit(1)
        # End try
        Len = file_len(f)
    else:
        f = sys.stdin
    # End if
    return (f, Len)
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
    if Dest == None:
        Dest = socket.gethostbyname(socket.gethostname())
    # End if
    if Port == None:
        Port = 10110
    # End if
    f = False
    sock = False
    try:
        (f, len) = openFile(fName)
        if len > 0:
            print("  UDP target IP: " + Dest)
            print("UDP target port: " + str(Port))
            print("Inserting %3.2f mS delay between each message." % (Delay*1000))
        sock = socket.socket(socket.AF_INET, # Internet
                            socket.SOCK_DGRAM) # UDP
        # Allow UDP broadcast
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        count = 0
        pct = percentComplete(5.0)
        while True :
            nextMessage = getNextMessage(f, Delay)
            count = count + 1
            pct.printPercent(count / len * 100)
            if not nextMessage:
                print("")
                Repeat -= 1
                if Repeat > 0:
                    f.seek(0)
                    count = 0
                    oldTime = time.perf_counter()
                    if Repeat > 1:
                        print("Repeating file...%d more times." % Repeat)
                    else:
                        print("Repeating file...%d more time." % Repeat)
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
    if Host == None:
        Host = socket.gethostbyname(socket.gethostname())
    # End if
    Host = socket.gethostbyname(Host)
    if Port == None:
        Port = 2947
    # End if
    f = False
    clients = []
    Server = False
    try:
        server_address = (Host, Port)
        Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Server.bind(server_address)
        Server.listen(5)
        listening = Server.getsockname()
        Server.setblocking(False)
        sel.register(Server, selectors.EVENT_READ, data=None)
        (f, len) = openFile(fName)
        if len > 0:
            print("Server at address: " + str(listening[0]) + " is listening on port: " + str(listening[1]))
        count = 0
        pct = percentComplete(5.0)
        while True :
            mess = getNextMessage(f, Delay)
            count = count + 1
            pct.printPercent(count / len * 100)
            if not mess:
                print("")
                Repeat -= 1
                if Repeat > 0:
                    f.seek(0)
                    count = 0
                    if Repeat > 1:
                        print("Repeating file...%d more times." % Repeat)
                    else:
                        print("Repeating file...%d more time." % Repeat)
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
        # Kill off the sockets
        for Client in clients:
            Client.close()
        if Server:
            Server.close()
        if f:
            f.close()
        # End if
        raise

    finally:
        for Client in clients:
            Client.close()
        if Server:
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
    print("")
    print("Options are case sensitive.")
    return
# End usage()

def main():
    # Set default options
    mode = 'UDP'
    Dest = None
    Host = None
    IPport = None
    td = 0.1
    Repeat = 1
    rCode = False

    # Pick up all commandline options
    try:
        options, remainder = getopt.gnu_getopt(sys.argv[1:], 'd:ho:p:rs:ut',
        ['dest=', 'help', 'host=', 'port=', 'repeat=', 'sleep=', 'UDP','TCP'])
        for opt, arg in options:
            if opt.lower() in ('-d', '--dest'):
                Dest = arg
            elif opt.lower() in ('-p', '--port'):
                IPport = int(arg)
            elif opt.lower() in ('-s', '--sleep'):
                td = float(arg)
            elif opt.lower() in ('-u', '--udp'):
                mode = 'UDP'
            elif opt.lower() in ('-t', '--tcp'):
                mode = 'TCP'
            elif opt in ('-o', '--host'):
                Host = arg
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
        if len(remainder) > 1:
            print("Please specify one file name containing NMEA data.")
            usage()
            sys.exit(1)
        # End if
        if len(remainder) == 0:
            fName = []
        else:
            fName = remainder[0]
        # End if
    except getopt.GetoptError as msg:
        print(msg)
        usage()
        sys.exit(2)
    # End try

    # Main program
    if mode.upper() == "UDP":
        rCode = udp(Dest, IPport, fName, td, Repeat)
    elif mode.upper() == "TCP":
        rCode = tcp(Host, IPport, fName, td, Repeat)
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
# End main()

if __name__ == "__main__":
    # execute only if run as a script
    main()
