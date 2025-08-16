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
import socket
import selectors
import types
import time
import getopt
import platform

# Platform-specific imports for preventing system sleep
try:
    if platform.system() == 'Windows':
        import ctypes
        from ctypes import wintypes
    elif platform.system() == 'Darwin':  # macOS
        import subprocess
    elif platform.system() == 'Linux':
        import subprocess
except ImportError:
    pass

assert sys.version_info >= (3, 5), "Must run in Python version 3.5 or above"

# Sleep interval (seconds) for TCP client connection polling
TCP_CLIENT_POLL_INTERVAL = 0.1

initialdelta = None
starttime = None

class SystemKeepAlive:
    """Cross-platform system keep-alive to prevent sleep during execution"""
    
    def __init__(self):
        self.system = platform.system()
        self.caffeinate_process = None
        self.active = False
    
    def prevent_sleep(self):
        """Prevent system from sleeping - cross-platform"""
        try:
            if self.system == 'Windows':
                # Windows: Use SetThreadExecutionState
                ctypes.windll.kernel32.SetThreadExecutionState(
                    0x80000000 |  # ES_CONTINUOUS
                    0x00000002 |  # ES_SYSTEM_REQUIRED
                    0x00000001     # ES_DISPLAY_REQUIRED
                )
                self.active = True
                print("Windows sleep prevention activated")
                
            elif self.system == 'Darwin':
                # macOS: Use caffeinate command
                self.caffeinate_process = subprocess.Popen(['caffeinate', '-d'])
                self.active = True
                print("macOS sleep prevention activated (caffeinate)")
                
            elif self.system == 'Linux':
                # Linux: Try to use systemd-inhibit or xset
                try:
                    # Try systemd-inhibit first (more modern)
                    subprocess.run(['systemd-inhibit', '--what=idle:sleep', '--who=VDRplayer', 
                                  '--why="NMEA data streaming"', '--mode=block', 'sleep', '1'], 
                                 check=True, capture_output=True)
                    print("Linux sleep prevention activated (systemd)")
                    self.active = True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    try:
                        # Fallback to xset (X11 systems)
                        subprocess.run(['xset', 's', 'off'], check=True, capture_output=True)
                        subprocess.run(['xset', '-dpms'], check=True, capture_output=True)
                        print("Linux sleep prevention activated (xset)")
                        self.active = True
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        print("Linux sleep prevention not available")
                        
        except Exception as e:
            print(f"Could not activate sleep prevention: {e}")
            self.active = False
    
    def allow_sleep(self):
        """Allow system to sleep again - cross-platform"""
        try:
            if self.system == 'Windows' and self.active:
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)  # ES_CONTINUOUS
                print("Windows sleep prevention deactivated")
                
            elif self.system == 'Darwin' and self.caffeinate_process:
                self.caffeinate_process.terminate()
                self.caffeinate_process.wait()
                print("macOS sleep prevention deactivated")
                
            elif self.system == 'Linux' and self.active:
                try:
                    # Re-enable screen saver and power management
                    subprocess.run(['xset', 's', 'on'], capture_output=True)
                    subprocess.run(['xset', '+dpms'], capture_output=True)
                    print("Linux sleep prevention deactivated")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
                    
        except Exception as e:
            print(f"Could not deactivate sleep prevention: {e}")
        finally:
            self.active = False
            self.caffeinate_process = None

# Global keep-alive instance
keep_alive = SystemKeepAlive()

class percentComplete:

    def __init__(self, tInc):
        self.oldTime = time.perf_counter()
        self.tInc = tInc

    def printPercent(self, percent):
        newTime = time.perf_counter()
        if (newTime - self.oldTime) > self.tInc:
            print(" %3.1f percent complete...." % round(percent, 1), end='\r')
            self.oldTime = newTime


# Count number of lines in a file
def lineCount(f):
    i = -1
    for (i, l) in enumerate(f):
        pass
    f.seek(0)
    return i + 1


def openFile(fName):
    Len = float('inf')
    if fName is not None:
        try:
            f = open(fName, 'r')
            print("Playing file '%s', Type Ctrl-C to exit..." % fName)
        except FileNotFoundError:
            print("File '%s' not found, exiting." % fName)
            sys.exit(1)
        # End try
        Len = lineCount(f)
    else:
        f = sys.stdin
    # End if
    return (f, Len)
# End openFile()


def getNextMessage(f, Delay, Speed):
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
    if Delay > 0:
        delayMessage(mess, Delay, Speed)
    mess = mess + u"\r\n"
    return(mess.encode("utf-8"))
# End getNextMessage()


def delayMessage(mess, Delay, Speed):
    global initialdelta
    global starttime

    # Check if it is a NMEAv4 message with timestamp
    try: 
       messtime = int(mess.split("*")[0].split(":")[2])
    except:
        time.sleep(Delay)
    else:
        if initialdelta is None:
            print("NMEAv4 timestamp found. Replaying logs at %3.2fx speed, instead of using delay." % Speed)
            starttime = time.time()
            initialdelta = starttime - messtime
        ComputedDelay = messtime + initialdelta - Speed * time.time() + (Speed - 1 ) * starttime
        if ComputedDelay > 60 :
            print("Huge gap in file. Not waiting %d seconds." % ComputedDelay)
            starttime = time.time()
            initialdelta = starttime - messtime
            ComputedDelay = 0 
        if ComputedDelay > 0 :
            time.sleep(ComputedDelay)
# End getMessageTimestamp()


def udp(Dest, Port, fName, Delay, Repeat, Speed):
    if Dest is None:
        Dest = socket.gethostbyname(socket.gethostname())
    # End if
    if Port is None:
        Port = 10110
    # End if
    f = False
    sock = False
    try:
        (f, len) = openFile(fName)
        if len > 0:
            print("  UDP target IP: " + Dest)
            print("UDP target port: " + str(Port))
            print("Inserting %3.2f mS delay between each message." %
                  (Delay * 1000))
        sock = socket.socket(socket.AF_INET,    # Internet
                             socket.SOCK_DGRAM)  # UDP
        # Allow UDP broadcast
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Add socket reuse for better cross-platform compatibility
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        count = 0
        pct = percentComplete(5.0)
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            nextMessage = getNextMessage(f, Delay, Speed)
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
            
            # Send next message to client with reasonable
            # number of retries before giving up.
            try:
                sock.sendto(nextMessage, (Dest, Port))
                consecutive_errors = 0  # Reset error counter on success
            except socket.error as e:
                consecutive_errors += 1
                print(f"\nSocket error: {e} (attempt {consecutive_errors})")
                if consecutive_errors >= max_consecutive_errors:
                    print("Too many consecutive socket errors, exiting...")
                    return False
                # Brief pause before retry
                time.sleep(0.1)
                continue
        # End while
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt.")
        return True
    # End except KeyboardInterrupt

    except Exception as ex:
        print("Exception...")
        print(ex)
        raise ex
    # End except Exception

    finally:
        if sock:
            sock.close()
        if f:
            f.close()
        # End if
    # End try
# End udp()


# Now we create the TCP version.
# It's more complex because we want to
# accept multiple client connections
# simultaneously.

sel = selectors.DefaultSelector()


def accept_wrapper(sock):
    conn, addr = sock.accept()
    conn.setblocking(False)
    client_data = types.SimpleNamespace(addr=addr, outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=client_data)
    print(f"Accepted connection from client: {client_data.addr}")
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
            return False
        # End if
    # End if
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]
        # End if
    # End if

    # Dynamically update selector events based on outb
    events = selectors.EVENT_READ
    if data.outb:
        events |= selectors.EVENT_WRITE
    try:
        sel.modify(sock, events, data=data)
    except Exception:
        pass

    return True
# End service_connection()


def tcp(Host, Port, fName, Delay, Repeat, Speed):
    if Host is None:
        Host = socket.gethostbyname(socket.gethostname())
    Host = socket.gethostbyname(Host)
    if Port is None:
        Port = 2947
    f = False
    Server = False
    try:
        server_address = (Host, Port)
        Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        
        # Add TCP keep-alive for better connection stability across platforms
        Server.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        
        # Platform-specific TCP keep-alive settings (where supported)
        try:
            if platform.system() != 'Windows':  # Unix-like systems
                Server.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
                Server.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
                Server.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
        except (AttributeError, OSError):
            pass  # Not all systems support these options
            
        Server.bind(server_address)
        Server.listen(5)
        listening = Server.getsockname()
        Server.setblocking(False)
        sel.register(Server, selectors.EVENT_READ, data=None)
        (f, length) = openFile(fName)
        if length > 0:
            print("Server at address: " + str(listening[0]) +
                  " is listening on port: " + str(listening[1]))
        count = 0
        pct = percentComplete(5.0)
        while True:
            # Wait for at least one client to be connected
            while True:
                events = sel.select(timeout=0)
                for key, mask in events:
                    if key.data is None:
                        accept_wrapper(key.fileobj)
                # Wait until at least one client connection is established
                # This checks if any registered socket has associated client data (i.e., is a client connection)
                if any(key.data is not None for key in sel.get_map().values()):
                    break
                time.sleep(TCP_CLIENT_POLL_INTERVAL)  # Wait a bit before checking again

            mess = getNextMessage(f, Delay, Speed)
            count += 1
            pct.printPercent(count / length * 100)
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

            # Send message to all connected clients
            for key in list(sel.get_map().values()):
                if key.data is not None:
                    try:
                        key.data.outb += mess
                        sel.modify(key.fileobj, selectors.EVENT_READ | selectors.EVENT_WRITE, data=key.data)
                    except Exception as ex:
                        print("Error updating client:", ex)
                        try:
                            sel.unregister(key.fileobj)
                        except Exception:
                            pass
                        key.fileobj.close()

            # Service all connections (send data if needed)
            events = sel.select(timeout=0)
            for key, mask in events:
                if key.data is not None:
                    try:
                        service_connection(key, mask)
                    except Exception as ex:
                        print("Error servicing client:", ex)
                        try:
                            sel.unregister(key.fileobj)
                        except Exception:
                            pass
                        key.fileobj.close()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt.")
        return True
    except Exception as ex:
        print("Exception...")
        print(ex)
        raise ex
    finally:
        for key in list(sel.get_map().values()):
            if key.data is not None:
                try:
                    sel.unregister(key.fileobj)
                except Exception:
                    pass
                key.fileobj.close()
        if Server:
            Server.close()
        if f:
            f.close()
# End tcp()


def usage():
    print("USAGE:")
    print("[python3] VDRplayer.py [--port=Port#] [--sleep=Sleep time] "
          "[--TCP --host=localhost | --UDP --dest=UDP_IP_Address] InputFile\n")
    print("Commandline options:\n")
    print("-d, --dest=IP_Address  UDP destination IP address.")
    print("                       Default will resolve to 'localhost'\n")
    print("-h, --help             print this message.\n")
    print("-o, --host=IP_Address  TCP server IP address.")
    print("                       This must resolve to a valid IP address on"
          " this computer.\n")
    print("-p, --port=#           optional communication port number.")
    print("                       Any valid port is accepted.\n")
    print("-r, --repeat=#         optional number of times to reread input"
          " file.\n")
    print("-s, --sleep=#.#        optional seconds delay between packets, when there is no timestamp in NMEA packets (NMEAv4).")
    print("                       default is 0.1 seconds.\n")
    print("-f, --fast=#.#         optional speed acceleration factor if NMEAv4.")
    print("                       default factor is 1.\n")
    print("-t, --TCP              create TCP server on primary IP address.")
    print("                       Specify local IP address using --host option"
          "\n                       to override default primary address.\n")
    print("-u, --UDP              create connectionless UDP link.")
    print("                       UDP is the default if no connection type"
          " specified.")
    print("                       Specify destination IP address using --dest"
          " option.\n")
    print("InputFile              Name of file containing NMEA message strings"
          ".")
    print("                       If no FILE is given then default is to read")
    print("                       input text from STDIN.\n")
    print("Options are case sensitive.")
    return
# End usage()


# This method returns the "primary" IP on the local box
# (the one with a default route). It may not be what you expect!
# (e.g. if you have multiple network interfaces)
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
# End get_pi()


def main():
    # Set default options
    mode = 'UDP'
    Dest = None
    Host = None
    IPport = None
    td = 0.1
    Repeat = 1
    rCode = False
    Speed=1

    # Activate cross-platform sleep prevention
    keep_alive.prevent_sleep()

    try:
        # Pick up all commandline options
        try:
            options, remainder = getopt.gnu_getopt(sys.argv[1:], 'd:ho:p:rs:utf:',
                                                   ['dest=',
                                                    'help',
                                                    'host=',
                                                    'port=',
                                                    'repeat=',
                                                    'sleep=',
                                                    'UDP',
                                                    'TCP',
                                                    'fast='])
            for opt, arg in options:
                if opt.lower() in ('-d', '--dest'):
                    mode = 'UDP'
                    Dest = arg
                elif opt.lower() in ('-p', '--port'):
                    IPport = int(arg)
                    if not (1 <= IPport <= 65535):
                        print("Error: Port must be between 1 and 65535")
                        sys.exit(2)
                elif opt.lower() in ('-s', '--sleep'):
                    td = float(arg)
                elif opt.lower() in ('-u', '--udp'):
                    mode = 'UDP'
                elif opt.lower() in ('-t', '--tcp'):
                    mode = 'TCP'
                elif opt in ('-o', '--host'):
                    mode = 'TCP'
                    Host = arg
                elif opt in ('-f', '--fast'):
                    Speed = float(arg)
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
            if len(remainder) < 1:
                print("Please specify one file name containing NMEA data.")
                usage()
                sys.exit(1)
            # End if
            if len(remainder) == 0:
                fName = []
            else:
                fName = remainder[0]
            if (Host is None) & (mode == 'TCP'):
                Host = get_ip()

            # End if
        except getopt.GetoptError as msg:
            print(msg)
            usage()
            sys.exit(2)
        # End try

        # Main program
        if mode.upper() == 'UDP':
            rCode = udp(Dest, IPport, fName, td, Repeat, Speed)
        elif mode.upper() == 'TCP':
            rCode = tcp(Host, IPport, fName, td, Repeat, Speed)
        else:
            usage()
        # End if
        
    finally:
        # Always restore sleep capability when exiting
        keep_alive.allow_sleep()
        
    if rCode is True:
        print("Exiting cleanly.")
        sys.exit(0)
    else:
        print("Something went wrong, exiting.")
        sys.exit(1)
    # End if
# End main()


if __name__ == '__main__':
    # execute only if run as a script
    main()
    