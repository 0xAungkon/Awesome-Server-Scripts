"""
This script displays network adapter details in a sorted tabular format by total RX+TX bytes.

Usage:
curl -s https://raw.githubusercontent.com/0xAungkon/Awesome-Server-Scripts/refs/heads/main/tabular-ifconfig.py | python3

Example output:
$ curl -s https://raw.githubusercontent.com/0xAungkon/Awesome-Server-Scripts/refs/heads/main/tabular-ifconfig.py | python3
Adapter             IPv4                MAC                 Gateway             RX             TX             
eth0                192.168.0.101       04:7c:16:1b:d9:9b   192.168.0.101       852.2 MB       296.2 MB       
tailscale0          100.84.159.117      N/A                 100.84.159.117      258.7 MB       154.1 MB       
lo                  N/A                 00:00:00:00:00:00   N/A                 22.7 MB        22.7 MB        
vetha290bae         N/A                 7e:c3:cd:40:fb:ba   N/A                 126.0 B        100.1 KB       
veth1fd2e34         N/A                 a2:63:6a:5a:f5:05   N/A                 284.0 B        99.6 KB        
veth58a4eac         N/A                 ba:ee:7e:6f:d2:ef   N/A                 126.0 B        95.6 KB        
veth3c7cc4f         N/A                 aa:68:bf:c7:82:13   N/A                 126.0 B        95.1 KB        
docker0             172.17.0.1          b6:d3:45:0f:48:a9   172.17.0.1          620.0 B        94.3 KB        
veth475a8a1         N/A                 e2:51:1e:bf:21:22   N/A                 126.0 B        94.5 KB        
veth761aa95         N/A                 fe:f5:94:7a:18:c0   N/A                 126.0 B        94.2 KB        
wlan0               N/A                 b6:38:11:ec:0a:a1   N/A                 N/A            N/A            
br-41b95eece985     192.168.49.1        7e:36:75:81:f0:30   192.168.49.1        0.0 B          0.0 B          
br-adf6ec7a0c28     172.18.0.1          52:a1:1f:15:ef:85   172.18.0.1          0.0 B          0.0 B          
br-051b5db25dfa     172.20.0.1          26:74:8d:22:54:3b   172.20.0.1          0.0 B          0.0 B          
br-3aa50eb1b644     172.19.0.1          c2:a4:63:00:32:c7   172.19.0.1          0.0 B          0.0 B          
"""

import subprocess
import re
import shutil
import socket

# ANSI color codes for terminal output formatting
YELLOW = '\033[93m'
GREEN = '\033[92m'
WHITE = '\033[97m'
GREY = '\033[90m'
RESET = '\033[0m'

def human_readable(bytes_str):
    """
    Convert bytes (string) to human-readable format (B, KB, MB, etc.)
    Returns 'N/A' if conversion fails.
    """
    try:
        b = int(bytes_str)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if b < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} PB"
    except:
        return 'N/A'

def total_bytes(rx, tx):
    """
    Calculate total bytes from RX and TX human-readable strings.
    Converts units back to bytes for sorting.
    """
    units = {'B': 1, 'KB': 1024, 'MB': 1048576, 'GB': 1073741824, 'TB': 1099511627776}
    def parse(val):
        try:
            num, unit = val.split()
            return float(num) * units[unit]
        except:
            return 0
    return parse(rx) + parse(tx)

# Run 'ip a' command to get network interface details
output = subprocess.check_output(['ip', 'a'], text=True)

adapters = []  # List to hold adapter dictionaries
current = {}   # Current adapter being processed

# Parse the 'ip a' output line by line
for line in output.splitlines():
    # Detect start of a new adapter block (e.g., "1: lo:")
    if re.match(r'^\d+:\s', line):
        if current:
            adapters.append(current)  # Save previous adapter info
        name = line.split(':')[1].strip()  # Extract adapter name
        test_name = name.split('@')[0] if '@' in name else name  # Remove '@' suffix if present
        # Validate adapter name using socket.if_nametoindex
        try:
            socket.if_nametoindex(name)
            valid_name = name
        except OSError:
            try:
                socket.if_nametoindex(test_name)
                valid_name = test_name
            except OSError:
                valid_name = name
        # Initialize adapter dict with default values
        current = {'Adapter': valid_name, 'IPv4': '', 'MAC': '', 'Gateway': 'N/A', 'RX': 'N/A', 'TX': 'N/A'}
    # Capture IPv4 address (only global scope)
    elif 'inet ' in line and 'scope global' in line:
        current['IPv4'] = re.search(r'inet ([\d\.]+)', line).group(1)
        current['Gateway'] = current['IPv4']
    # Capture MAC address line
    elif 'link/' in line:
        mac = re.search(r'link/\w+\s+([\da-f:]{17})', line)
        if mac:
            current['MAC'] = mac.group(1)

# Add last adapter after loop ends
if current:
    adapters.append(current)

# Check if 'ifconfig' command is available
ifconfig_exists = shutil.which('ifconfig') is not None

if ifconfig_exists:
    try:
        # Get ifconfig output for RX/TX bytes
        ifconfig_out = subprocess.check_output(['ifconfig'], text=True)
        for adapter in adapters:
            # Regex pattern to extract RX and TX packets/bytes for each adapter
            pattern = re.compile(rf"^{adapter['Adapter']}.*?(RX packets.*?TX packets.*?)\n\n", re.DOTALL | re.MULTILINE)
            match = pattern.search(ifconfig_out)
            if match:
                stats = match.group(1)
                # Extract RX bytes
                rx = re.search(r'RX packets \d+\s+bytes\s+(\d+)', stats)
                # Extract TX bytes
                tx = re.search(r'TX packets \d+\s+bytes\s+(\d+)', stats)
                if rx:
                    adapter['RX'] = human_readable(rx.group(1))
                if tx:
                    adapter['TX'] = human_readable(tx.group(1))
    except Exception:
        pass

# Sort adapters by total RX+TX bytes in descending order
adapters.sort(key=lambda x: total_bytes(x['RX'], x['TX']), reverse=True)

# Print header row with column titles
print(f"{'Adapter':<20}{'IPv4':<20}{'MAC':<20}{'Gateway':<20}{'RX':<15}{'TX':<15}")

# Print adapter info rows with color formatting
for a in adapters:
    adapter = f"{YELLOW}{a['Adapter']:<20}{RESET}"
    ipv4 = a['IPv4'] if a['IPv4'] else 'N/A'
    mac = a['MAC'] if a['MAC'] else 'N/A'
    gateway = a['Gateway'] if a['Gateway'] else "N/A"
    rx = a['RX']
    tx = a['TX']

    ipv4_color = f"{GREEN}{ipv4:<20}{RESET}" if a['IPv4'] else f"{GREY}{ipv4:<20}{RESET}"
    mac_color = f"{WHITE}{mac:<20}{RESET}" if a['MAC'] else f"{GREY}{mac:<20}{RESET}"
    gateway_color = f"{GREEN}{gateway:<20}{RESET}" if gateway != 'N/A' else f"{GREY}{gateway:<20}{RESET}"
    rx_color = f"{WHITE}{rx:<15}{RESET}" if rx != 'N/A' else f"{GREY}{rx:<15}{RESET}"
    tx_color = f"{WHITE}{tx:<15}{RESET}" if tx != 'N/A' else f"{GREY}{tx:<15}{RESET}"

    print(f"{adapter}{ipv4_color}{mac_color}{gateway_color}{rx_color}{tx_color}")

# Warn if ifconfig command not found and RX/TX info was skipped
if not ifconfig_exists:
    print(f"{GREY}[!] Warning: ifconfig not available, skipping RX/TX/Gateway info{RESET}")
