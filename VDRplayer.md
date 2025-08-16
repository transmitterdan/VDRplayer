# VDRplayer.py - Cross-Platform NMEA Data Player

## Purpose

VDRplayer.py is a Python 3 application designed to replay NMEA (National Marine Electronics Association) data streams from files or stdin. It supports both UDP broadcast and TCP server modes with cross-platform compatibility, making it useful for testing marine navigation systems, GPS applications, and other software that consumes NMEA data.

The program includes advanced features like system sleep prevention, NMEAv4 timestamp-based replay, and robust error handling to ensure continuous operation across Windows, macOS, and Linux systems.

## How It Works

### Core Functionality
- **File Processing**: Reads NMEA messages line by line from input files or stdin
- **Network Distribution**: Sends messages via UDP broadcast or TCP server connections
- **Timing Control**: Supports both fixed delays and NMEAv4 timestamp-based replay with speed acceleration
- **Progress Tracking**: Shows real-time completion percentage during playbook
- **Repeat Capability**: Can replay files multiple times automatically
- **Cross-Platform Sleep Prevention**: Prevents system sleep/hibernation during operation
- **Error Recovery**: Handles network errors gracefully with retry logic

### Network Modes

#### UDP Mode (Default)
- Broadcasts NMEA messages to specified IP address and port
- Connectionless with automatic error recovery
- Socket reuse and broadcast optimization
- Default port: 10110

#### TCP Mode
- Creates a TCP server that accepts multiple client connections
- Uses asynchronous I/O with selectors for efficient client management
- TCP keep-alive support for connection stability
- Waits for at least one client before starting playback
- Default port: 2947

### Cross-Platform Features

#### System Sleep Prevention
- **Windows**: Uses `SetThreadExecutionState` API to prevent sleep and display timeout
- **macOS**: Uses `caffeinate` command to maintain system activity
- **Linux**: Uses `systemd-inhibit` or falls back to `xset` for X11 systems
- Automatically restores normal power management on exit

## Classes Reference

### `SystemKeepAlive`
**Purpose**: Cross-platform system sleep prevention
- `__init__()`: Initialize for current platform
- `prevent_sleep()`: Activate sleep prevention using platform-specific methods
- `allow_sleep()`: Restore normal power management

#### Platform-Specific Behavior:
- **Windows**: Prevents system and display sleep using kernel32 API
- **macOS**: Launches caffeinate subprocess to prevent display sleep
- **Linux**: Uses systemd-inhibit or xset commands as available

### `percentComplete`
**Purpose**: Real-time progress tracking with time-based updates
- `__init__(tInc)`: Initialize with time increment for throttled updates
- `printPercent(percent)`: Display progress only after specified time interval

## Functions Reference

### File Operations

#### `lineCount(f)`
**Purpose**: Efficiently count total lines in file for progress calculation
- Pre-scans entire file and resets file pointer
- Returns accurate line count for progress percentage

#### `openFile(fName)`
**Purpose**: Robust file opening with error handling
- Opens specified file or uses stdin if no filename provided
- Handles FileNotFoundError with graceful exit
- Returns file handle and total line count

#### `getNextMessage(f, Delay, Speed)`
**Purpose**: Read and process next NMEA message
- Reads line, strips whitespace, adds proper CRLF termination
- Applies timing delays through `delayMessage()`
- Returns UTF-8 encoded message ready for transmission
- Returns False at end of file

#### `delayMessage(mess, Delay, Speed)`
**Purpose**: Intelligent timing control for realistic playback
- **NMEAv4 Mode**: Detects timestamps and calculates real-time delays
- **Fixed Delay Mode**: Uses specified delay when no timestamps found
- **Speed Control**: Supports acceleration/deceleration for NMEAv4 replay
- **Gap Handling**: Prevents excessive delays from large timestamp gaps

### Network Functions

#### `udp(Dest, Port, fName, Delay, Repeat, Speed)`
**Purpose**: UDP broadcast with enhanced reliability
- Sets up UDP socket with broadcast and reuse capabilities
- Implements error recovery with consecutive error counting
- Handles file repetition and progress display
- Graceful shutdown on keyboard interrupt or fatal errors

**Enhanced Features**:
- Consecutive error tracking (max 5 failures before exit)
- Socket option optimization for cross-platform compatibility
- Automatic retry with brief delays on transient errors

#### `tcp(Host, Port, fName, Delay, Repeat, Speed)`
**Purpose**: Multi-client TCP server with advanced connection management
- Creates non-blocking TCP server with keep-alive support
- Uses selector-based I/O for efficient multi-client handling
- Platform-specific TCP optimizations (keep-alive parameters)
- Robust client connection and disconnection handling

**Enhanced Features**:
- TCP keep-alive configuration for connection stability
- Dynamic selector event management
- Comprehensive error handling for client operations
- Graceful cleanup of all connections on exit

#### `accept_wrapper(sock)`
**Purpose**: Handle new TCP client connections
- Accepts and configures new client connections
- Sets non-blocking mode and creates client data structures
- Registers clients with main selector for I/O monitoring

#### `service_connection(key, mask)`
**Purpose**: Service active TCP client connections
- Handles both read and write events for clients
- Manages client disconnections and cleanup
- Dynamically updates selector events based on output buffer state
- Returns connection status for error handling

### Utility Functions

#### `usage()`
**Purpose**: Comprehensive command-line help display
- Shows all available options with detailed descriptions
- Includes usage examples and default values

#### `get_ip()`
**Purpose**: Determine primary local IP address
- Uses dummy connection technique to find default route IP
- Falls back to localhost on network errors
- Cross-platform compatible implementation

#### `main()`
**Purpose**: Program entry point and coordination
- Parses command-line arguments with GNU-style option handling
- Activates cross-platform sleep prevention
- Coordinates between UDP and TCP modes
- Ensures proper cleanup with try/finally blocks

## Command Line Options

```bash
python3 VDRplayer.py [options] InputFile

Network Options:
-d, --dest=IP_Address    UDP destination IP address (default: localhost)
-o, --host=IP_Address    TCP server IP address (default: primary interface)
-p, --port=#             Communication port number (UDP: 10110, TCP: 2947)
-t, --TCP                Use TCP server mode
-u, --UDP                Use UDP broadcast mode (default)

Timing Options:
-s, --sleep=#.#          Delay between packets in seconds (default: 0.1)
-f, --fast=#.#           Speed acceleration factor for NMEAv4 (default: 1.0)

Playback Options:
-r, --repeat=#           Number of times to repeat file (default: 1)
-h, --help               Show detailed help message

File Input:
InputFile                NMEA data file (uses stdin if not specified)
```

## Example Usage

```bash
# Basic UDP broadcast to localhost
python3 VDRplayer.py nmea_data.txt

# TCP server with specific interface and port
python3 VDRplayer.py --TCP --host=192.168.1.100 --port=2947 nmea_data.txt

# UDP broadcast to specific destination
python3 VDRplayer.py --UDP --dest=192.168.1.255 --port=10110 nmea_data.txt

# Repeat file with custom delays
python3 VDRplayer.py --repeat=5 --sleep=0.5 nmea_data.txt

# Fast NMEAv4 replay at 2x speed
python3 VDRplayer.py --TCP --fast=2.0 timestamped_nmea.txt

# Read from stdin with TCP server
cat nmea_data.txt | python3 VDRplayer.py --TCP
```

## Cross-Platform Compatibility

### Supported Operating Systems
- **Windows 7+**: Full functionality including sleep prevention
- **macOS 10.9+**: Requires `caffeinate` command (standard on modern macOS)
- **Linux**: Works on most distributions, enhanced features with systemd or X11

### Dependencies
- **Python 3.5+**: Core requirement
- **Standard Library Only**: No external packages required
- **Platform Tools**: Uses system utilities when available (caffeinate, systemd-inhibit, xset)

### Known Limitations
- Linux sleep prevention requires systemd or X11 environment
- Some TCP keep-alive options not available on all platforms
- macOS requires administrative privileges for some network operations in certain configurations

## Technical Implementation Details

### Socket Configuration
- **UDP**: Broadcast enabled, address reuse, optimized for connectionless operation
- **TCP**: Keep-alive enabled, non-blocking I/O, multiple client support
- **Error Handling**: Comprehensive exception catching with graceful degradation

### Timing Implementation
- **NMEAv4 Detection**: Parses timestamp from message format `*XX:TIMESTAMP`
- **Real-time Simulation**: Calculates delays based on original timestamps
- **Speed Control**: Adjusts playback speed while maintaining relative timing
- **Gap Protection**: Prevents excessive delays from timestamp discontinuities

### Memory Management
- **Streaming Processing**: Processes files line-by-line to minimize memory usage
- **Client Buffering**: Individual output buffers for each TCP client
- **Resource Cleanup**: Comprehensive cleanup in finally blocks

## Troubleshooting

### Common Issues
1. **Screen Lock Problems**: Ensure sleep prevention activated (check startup messages)
2. **Network Errors**: Verify firewall settings and port availability
3. **Permission Errors**: Some platforms require elevated privileges for certain operations
4. **File Access**: Ensure input files are accessible and properly formatted

### Debug Information
- Program shows sleep prevention status on startup
- Network configuration displayed when connections established
- Progress updates every 5 seconds during playback
- Error messages include specific exception details

## Future Improvements

### Planned Enhancements
- **Configuration File Support**: YAML/JSON configuration files
- **Enhanced Logging**: Structured logging with configurable levels
- **Performance Metrics**: Detailed statistics and performance monitoring
- **Protocol Validation**: NMEA sentence validation and checksum verification
- **GUI Interface**: Cross-platform graphical interface
- **WebSocket Support**: Modern web application compatibility

### Code Quality Improvements
- **Type Annotations**: Full Python type hints
- **Unit Testing**: Comprehensive test suite
- **Documentation**: Enhanced docstrings and API documentation
- **Packaging**: Proper Python package structure with setup.py