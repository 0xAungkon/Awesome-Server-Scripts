import subprocess
import re
import shutil
import socket

YELLOW = '\033[93m'
GREEN = '\033[92m'
WHITE = '\033[97m'
GREY = '\033[90m'
RESET = '\033[0m'

def human_readable(bytes_str):
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
    units = {'B': 1, 'KB': 1024, 'MB': 1048576, 'GB': 1073741824, 'TB': 1099511627776}
    def parse(val):
        try:
            num, unit = val.split()
            return float(num) * units[unit]
        except:
            return 0
    return parse(rx) + parse(tx)

output = subprocess.check_output(['ip', 'a'], text=True)
adapters = []
current = {}

for line in output.splitlines():
    if re.match(r'^\d+:\s', line):
        if current:
            adapters.append(current)
        name = line.split(':')[1].strip()
        test_name = name.split('@')[0] if '@' in name else name
        try:
            socket.if_nametoindex(name)
            valid_name = name
        except OSError:
            try:
                socket.if_nametoindex(test_name)
                valid_name = test_name
            except OSError:
                valid_name = name
        current = {'Adapter': valid_name, 'IPv4': '', 'MAC': '', 'Gateway': 'N/A', 'RX': 'N/A', 'TX': 'N/A'}
    elif 'inet ' in line and 'scope global' in line:
        current['IPv4'] = re.search(r'inet ([\d\.]+)', line).group(1)
        current['Gateway'] = current['IPv4']
    elif 'link/' in line:
        mac = re.search(r'link/\w+\s+([\da-f:]{17})', line)
        if mac:
            current['MAC'] = mac.group(1)

if current:
    adapters.append(current)

ifconfig_exists = shutil.which('ifconfig') is not None
if ifconfig_exists:
    try:
        ifconfig_out = subprocess.check_output(['ifconfig'], text=True)
        for adapter in adapters:
            pattern = re.compile(rf"^{adapter['Adapter']}.*?(RX packets.*?TX packets.*?)\n\n", re.DOTALL | re.MULTILINE)
            match = pattern.search(ifconfig_out)
            if match:
                stats = match.group(1)
                rx = re.search(r'RX packets \d+\s+bytes\s+(\d+)', stats)
                tx = re.search(r'TX packets \d+\s+bytes\s+(\d+)', stats)
                if rx:
                    adapter['RX'] = human_readable(rx.group(1))
                if tx:
                    adapter['TX'] = human_readable(tx.group(1))
    except Exception:
        pass

adapters.sort(key=lambda x: total_bytes(x['RX'], x['TX']), reverse=True)

print(f"{'Adapter':<20}{'IPv4':<20}{'MAC':<20}{'Gateway':<20}{'RX':<15}{'TX':<15}")
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

if not ifconfig_exists:
    print(f"{GREY}[!] Warning: ifconfig not available, skipping RX/TX/Gateway info{RESET}")
