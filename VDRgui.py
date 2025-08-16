#!/usr/bin/env python3
"""
VDRplayer GUI - Graphical interface for VDRplayer.py
Provides an easy-to-use interface for setting up NMEA data playback
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import socket
import platform
from pathlib import Path

class VDRPlayerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VDRplayer - NMEA Data Player")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        # Process tracking
        self.vdr_process = None
        self.is_running = False
        
        # Create GUI elements
        self.create_widgets()
        self.load_defaults()
        
    def create_widgets(self):
        # Create main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="NMEA Data Player Configuration", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File Selection Section
        file_frame = ttk.LabelFrame(main_frame, text="Input File", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="NMEA Data File:").grid(row=0, column=0, sticky=tk.W)
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, width=50)
        self.file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5))
        
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).grid(row=0, column=2)
        
        # Network Configuration Section
        network_frame = ttk.LabelFrame(main_frame, text="Network Configuration", padding="10")
        network_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        network_frame.columnconfigure(1, weight=1)
        
        # Protocol selection
        ttk.Label(network_frame, text="Protocol:").grid(row=0, column=0, sticky=tk.W)
        self.protocol_var = tk.StringVar(value="UDP")
        protocol_frame = ttk.Frame(network_frame)
        protocol_frame.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Radiobutton(protocol_frame, text="UDP", variable=self.protocol_var, 
                       value="UDP", command=self.protocol_changed).pack(side=tk.LEFT)
        ttk.Radiobutton(protocol_frame, text="TCP", variable=self.protocol_var, 
                       value="TCP", command=self.protocol_changed).pack(side=tk.LEFT, padx=(20, 0))
        
        # IP Address
        ttk.Label(network_frame, text="IP Address:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.ip_var = tk.StringVar()
        self.ip_entry = ttk.Entry(network_frame, textvariable=self.ip_var, width=20)
        self.ip_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        # Auto-detect IP button
        ttk.Button(network_frame, text="Auto-detect", command=self.auto_detect_ip).grid(row=1, column=2, padx=(10, 0), pady=(5, 0))
        
        # Port
        ttk.Label(network_frame, text="Port:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.port_var = tk.StringVar()
        port_frame = ttk.Frame(network_frame)
        port_frame.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        self.port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=10)
        self.port_entry.pack(side=tk.LEFT)
        
        # Default port button
        ttk.Button(port_frame, text="Default", command=self.set_default_port).pack(side=tk.LEFT, padx=(10, 0))
        
        # IP address label (shows UDP destination vs TCP host)
        self.ip_label_var = tk.StringVar(value="UDP Destination:")
        self.ip_label = ttk.Label(network_frame, textvariable=self.ip_label_var)
        self.ip_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Timing Configuration Section
        timing_frame = ttk.LabelFrame(main_frame, text="Timing Configuration", padding="10")
        timing_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        timing_frame.columnconfigure(1, weight=1)
        
        # Sleep delay
        ttk.Label(timing_frame, text="Delay between packets (seconds):").grid(row=0, column=0, sticky=tk.W)
        self.sleep_var = tk.StringVar(value="0.1")
        sleep_spin = ttk.Spinbox(timing_frame, from_=0.001, to=60.0, increment=0.1, 
                                textvariable=self.sleep_var, width=10, format="%.3f")
        sleep_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Speed factor
        ttk.Label(timing_frame, text="Speed factor (NMEAv4):").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.speed_var = tk.StringVar(value="1.0")
        speed_spin = ttk.Spinbox(timing_frame, from_=0.1, to=10.0, increment=0.1, 
                                textvariable=self.speed_var, width=10, format="%.1f")
        speed_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        # Repeat count
        ttk.Label(timing_frame, text="Repeat count:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.repeat_var = tk.StringVar(value="1")
        repeat_spin = ttk.Spinbox(timing_frame, from_=1, to=1000, increment=1, 
                                 textvariable=self.repeat_var, width=10)
        repeat_spin.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        # Advanced Options Section
        advanced_frame = ttk.LabelFrame(main_frame, text="Advanced Options", padding="10")
        advanced_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Custom command line arguments
        ttk.Label(advanced_frame, text="Additional arguments:").grid(row=0, column=0, sticky=tk.W)
        self.custom_args_var = tk.StringVar()
        custom_args_entry = ttk.Entry(advanced_frame, textvariable=self.custom_args_var, width=50)
        custom_args_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        advanced_frame.columnconfigure(1, weight=1)
        
        # Control Buttons Section
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="Start VDRplayer", 
                                      command=self.start_vdrplayer, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                     command=self.stop_vdrplayer, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Test Configuration", 
                  command=self.test_configuration).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Save Config", 
                  command=self.save_configuration).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Load Config", 
                  command=self.load_configuration).pack(side=tk.LEFT)
        
        # Status and Output Section
        output_frame = ttk.LabelFrame(main_frame, text="Status and Output", padding="10")
        output_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(output_frame, textvariable=self.status_var, 
                                font=('Arial', 9), foreground='blue')
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame, height=12, width=70)
        self.output_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        # Clear output button
        ttk.Button(output_frame, text="Clear Output", 
                  command=self.clear_output).grid(row=2, column=0, sticky=tk.E, pady=(5, 0))
    
    def load_defaults(self):
        """Load default values"""
        self.auto_detect_ip()
        self.set_default_port()
        self.protocol_changed()
        
    def browse_file(self):
        """Browse for NMEA data file"""
        filename = filedialog.askopenfilename(
            title="Select NMEA Data File",
            filetypes=[
                ("Text files", "*.txt"),
                ("NMEA files", "*.nmea"),
                ("Log files", "*.log"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.file_var.set(filename)
    
    def protocol_changed(self):
        """Update UI based on protocol selection"""
        if self.protocol_var.get() == "UDP":
            self.ip_label_var.set("UDP Destination:")
            self.set_default_port()
        else:
            self.ip_label_var.set("TCP Host:")
            self.set_default_port()
    
    def auto_detect_ip(self):
        """Auto-detect the primary IP address"""
        try:
            # Use the same method as VDRplayer.py
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
            s.close()
            self.ip_var.set(ip)
        except Exception:
            self.ip_var.set('127.0.0.1')
    
    def set_default_port(self):
        """Set default port based on protocol"""
        if self.protocol_var.get() == "UDP":
            self.port_var.set("10110")
        else:
            self.port_var.set("2947")
    
    def validate_configuration(self):
        """Validate the current configuration"""
        errors = []
        
        # Check file
        if not self.file_var.get():
            errors.append("Please select an input file")
        elif not os.path.exists(self.file_var.get()):
            errors.append("Selected file does not exist")
        
        # Check IP address
        if not self.ip_var.get():
            errors.append("Please specify an IP address")
        else:
            try:
                # Accept both IP addresses and hostnames like 'localhost'
                try:
                    socket.inet_aton(self.ip_var.get())
                except socket.error:
                    # Try to resolve as hostname
                    try:
                        socket.gethostbyname(self.ip_var.get())
                    except socket.error:
                        errors.append("Invalid IP address or hostname format")
            except socket.error:
                errors.append("Invalid IP address format")
        
        # Check port
        try:
            port = int(self.port_var.get())
            if not (1 <= port <= 65535):
                errors.append("Port must be between 1 and 65535")
        except ValueError:
            errors.append("Port must be a valid number")
        
        # Check timing values
        try:
            sleep_val = float(self.sleep_var.get())
            if sleep_val < 0:
                errors.append("Sleep delay must be non-negative")
        except ValueError:
            errors.append("Sleep delay must be a valid number")
        
        try:
            speed_val = float(self.speed_var.get())
            if speed_val <= 0:
                errors.append("Speed factor must be positive")
        except ValueError:
            errors.append("Speed factor must be a valid number")
        
        try:
            repeat_val = int(self.repeat_var.get())
            if repeat_val < 1:
                errors.append("Repeat count must be at least 1")
        except ValueError:
            errors.append("Repeat count must be a valid integer")
        
        return errors
    
    def test_configuration(self):
        """Test the current configuration without starting VDRplayer"""
        errors = self.validate_configuration()
        
        if errors:
            messagebox.showerror("Configuration Errors", "\n".join(errors))
            return
        
        # Build command line for testing
        cmd_args = self.build_command_line(dry_run=True)
        
        test_info = f"Configuration Test Results:\n\n"
        test_info += f"Command that would be executed:\n"
        test_info += f"python {' '.join(cmd_args)}\n\n"
        test_info += f"Protocol: {self.protocol_var.get()}\n"
        test_info += f"IP Address: {self.ip_var.get()}\n"
        test_info += f"Port: {self.port_var.get()}\n"
        test_info += f"Input File: {self.file_var.get()}\n"
        test_info += f"Sleep Delay: {self.sleep_var.get()}s\n"
        test_info += f"Speed Factor: {self.speed_var.get()}x\n"
        test_info += f"Repeat Count: {self.repeat_var.get()}\n"
        
        messagebox.showinfo("Configuration Test", test_info)
    
    def build_command_line(self, dry_run=False):
        """Build command line arguments for VDRplayer"""
        # Find VDRplayer.py script
        script_dir = Path(__file__).parent
        vdrplayer_path = script_dir / "VDRplayer.py"
        
        if not vdrplayer_path.exists():
            vdrplayer_path = "VDRplayer.py"  # Hope it's in PATH
        
        args = [str(vdrplayer_path)]
        
        # Protocol and network settings
        if self.protocol_var.get() == "UDP":
            args.extend(["--UDP", "--dest", self.ip_var.get()])
        else:
            args.extend(["--TCP", "--host", self.ip_var.get()])
        
        # Port
        args.extend(["--port", self.port_var.get()])
        
        # Timing settings
        args.extend(["--sleep", self.sleep_var.get()])
        args.extend(["--fast", self.speed_var.get()])
        args.extend(["--repeat", self.repeat_var.get()])
        
        # Custom arguments
        if self.custom_args_var.get():
            args.extend(self.custom_args_var.get().split())
        
        # Input file
        args.append(self.file_var.get())
        
        return args
    
    def start_vdrplayer(self):
        """Start VDRplayer process"""
        if self.is_running:
            messagebox.showwarning("Already Running", "VDRplayer is already running")
            return
        
        # Validate configuration
        errors = self.validate_configuration()
        if errors:
            messagebox.showerror("Configuration Errors", "\n".join(errors))
            return
        
        try:
            # Build command
            args = self.build_command_line()
            
            # Update status
            self.status_var.set("Starting VDRplayer...")
            self.log_output(f"Starting VDRplayer with command: python {' '.join(args)}")
            
            # Start process
            self.vdr_process = subprocess.Popen(
                [sys.executable] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.is_running = True
            self.start_button.configure(state=tk.DISABLED)
            self.stop_button.configure(state=tk.NORMAL)
            self.status_var.set("VDRplayer running...")
            
            # Start thread to monitor output
            threading.Thread(target=self.monitor_process, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start VDRplayer: {str(e)}")
            self.status_var.set("Error starting VDRplayer")
    
    def stop_vdrplayer(self):
        """Stop VDRplayer process"""
        if self.vdr_process and self.is_running:
            try:
                self.vdr_process.terminate()
                self.vdr_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.vdr_process.kill()
                self.vdr_process.wait()
            except Exception as e:
                self.log_output(f"Error stopping process: {e}")
            
            self.cleanup_process()
    
    def cleanup_process(self):
        """Clean up after process ends"""
        self.is_running = False
        self.vdr_process = None
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.status_var.set("VDRplayer stopped")
        self.log_output("VDRplayer process ended")
    
    def monitor_process(self):
        """Monitor VDRplayer output in background thread"""
        try:
            while self.is_running and self.vdr_process:
                line = self.vdr_process.stdout.readline()
                if line:
                    # Update UI from background thread
                    self.root.after(0, self.log_output, line.rstrip())
                elif self.vdr_process.poll() is not None:
                    break
        except Exception as e:
            self.root.after(0, self.log_output, f"Error monitoring process: {e}")
        finally:
            if self.vdr_process and self.vdr_process.poll() is not None:
                self.root.after(0, self.cleanup_process)
    
    def log_output(self, message):
        """Add message to output text area"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
    
    def clear_output(self):
        """Clear the output text area"""
        self.output_text.delete(1.0, tk.END)
    
    def save_configuration(self):
        """Save current configuration to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".cfg",
            filetypes=[("Config files", "*.cfg"), ("All files", "*.*")]
        )
        if filename:
            try:
                config = {
                    'protocol': self.protocol_var.get(),
                    'ip_address': self.ip_var.get(),
                    'port': self.port_var.get(),
                    'input_file': self.file_var.get(),
                    'sleep_delay': self.sleep_var.get(),
                    'speed_factor': self.speed_var.get(),
                    'repeat_count': self.repeat_var.get(),
                    'custom_args': self.custom_args_var.get()
                }
                
                with open(filename, 'w') as f:
                    for key, value in config.items():
                        f.write(f"{key}={value}\n")
                
                messagebox.showinfo("Success", f"Configuration saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_configuration(self):
        """Load configuration from file"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("Config files", "*.cfg"), ("All files", "*.*")]
        )
        if filename:
            try:
                config = {}
                with open(filename, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key] = value
                
                # Apply configuration
                if 'protocol' in config:
                    self.protocol_var.set(config['protocol'])
                if 'ip_address' in config:
                    self.ip_var.set(config['ip_address'])
                if 'port' in config:
                    self.port_var.set(config['port'])
                if 'input_file' in config:
                    self.file_var.set(config['input_file'])
                if 'sleep_delay' in config:
                    self.sleep_var.set(config['sleep_delay'])
                if 'speed_factor' in config:
                    self.speed_var.set(config['speed_factor'])
                if 'repeat_count' in config:
                    self.repeat_var.set(config['repeat_count'])
                if 'custom_args' in config:
                    self.custom_args_var.set(config['custom_args'])
                
                self.protocol_changed()  # Update UI
                messagebox.showinfo("Success", f"Configuration loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def on_closing(self):
        """Handle application closing"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "VDRplayer is still running. Stop it and quit?"):
                self.stop_vdrplayer()
                self.root.after(1000, self.root.destroy)  # Give time to clean up
        else:
            self.root.destroy()

def main():
    """Main entry point for the GUI application"""
    root = tk.Tk()
    
    # Set up modern theme if available
    try:
        style = ttk.Style()
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
    except Exception:
        pass  # Use default theme
    
    # Create and configure main application
    app = VDRPlayerGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # Start the GUI
    root.mainloop()

if __name__ == '__main__':
    main()