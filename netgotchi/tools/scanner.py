"""
netgotchi.tools.scanner
~~~~~~~~~~~~~~~~~~~~~~~
Nmap network scanner wrapper using python-nmap.

LEARNING NOTES — this module teaches:
  - The python-nmap library (Pythonic nmap interface)
  - Network scanning concepts (host discovery, port scanning)
  - Dictionary iteration and data extraction patterns  
  - How network engineers discover what's on a network

WHAT IS NMAP?
    Nmap ("Network Mapper") is the most widely used network scanner.
    It discovers hosts and services on a network by sending packets
    and analyzing responses. It can:
    - Find which hosts are alive on a subnet ("ping sweep")
    - Discover open ports and running services
    - Detect operating systems and software versions
    
    python-nmap is a Python wrapper that lets you control nmap and
    parse its results from Python code.

IMPORTANT — NMAP MUST BE INSTALLED:
    python-nmap is just a wrapper. You need the actual nmap binary:
    sudo apt install nmap   (Debian/Ubuntu)
    brew install nmap       (macOS)
"""

from .base import BaseTool

try:
    import nmap
    HAS_NMAP = True
except ImportError:
    HAS_NMAP = False


class ScannerTool(BaseTool):
    """Network scanner using nmap.

    Usage:
        scanner = ScannerTool()
        scanner.run({
            "target": "192.168.1.0/24",
            "scan_type": "quick",
        }, callback=handle_result)
    """

    @property
    def name(self):
        return "Nmap"

    def _execute(self, params):
        """Run an nmap scan and parse results.

        LEARNING NOTE — nmap.PortScanner():
            This is the main python-nmap class. Key methods:
            
            nm.scan(hosts, ports, arguments):
                hosts: Target IP, range, or CIDR (e.g., "192.168.1.0/24")
                ports: Port range string (e.g., "22-443")
                arguments: nmap flags as string (e.g., "-sV" for version detect)
            
            nm.all_hosts():
                Returns list of all discovered host IPs.
            
            nm[host]:
                Dict-like access to host data.
                nm[host].state()        → 'up' or 'down'
                nm[host].all_protocols() → ['tcp', 'udp']
                nm[host]['tcp']          → dict of {port: info}

        Args:
            params: Dict with:
                target (str): IP, range, or CIDR subnet.
                scan_type (str): "quick", "ports", or "full".
                ports (str): Port range (optional, for "ports" scan).

        Returns:
            Dict with discovered hosts and services.
        """

        if not HAS_NMAP:
            return {
                "hosts": [],
                "host_count": 0,
                "error": "python-nmap not installed! Run: pip install python-nmap",
            }

        target = params.get("target", "")
        scan_type = params.get("scan_type", "full")
        ports = params.get("ports", "22,80,443")

        nm = nmap.PortScanner()

        # LEARNING NOTE — scan types:
        #   -sn     = "ping scan" — just check if hosts are alive (no port scan)
        #   -sT     = TCP connect scan — full TCP handshake per port
        #   -sV     = Version detection — probe open ports for service info
        #   -F      = Fast scan — only scan top 100 ports
        #   -T4     = Aggressive timing — faster but noisier
        scan_args = {
            "quick": "-sn",           # Just host discovery (fastest)
            "ports": f"-sT -p {ports}",  # Scan specific ports
            "full": "-sT -sV -F",     # Port scan + version detection
        }

        arguments = scan_args.get(scan_type, "-sn")

        try:
            nm.scan(hosts=target, arguments=arguments)
        except nmap.PortScannerError as e:
            return {
                "hosts": [],
                "host_count": 0,
                "error": f"Nmap error: {e}",
            }

        # LEARNING NOTE — building result data:
        #   We iterate through nmap's results and build a clean dict
        #   that our UI layer can easily display. This is a common
        #   pattern: parse complex output into simple structured data.
        hosts = []
        for host_ip in nm.all_hosts():
            host_data = {
                "ip": host_ip,
                "state": nm[host_ip].state(),
                "hostname": nm[host_ip].hostname(),
                "ports": [],
            }

            # Extract port information if available
            for proto in nm[host_ip].all_protocols():
                for port in nm[host_ip][proto]:
                    port_info = nm[host_ip][proto][port]
                    host_data["ports"].append({
                        "port": port,
                        "protocol": proto,
                        "state": port_info.get("state", "unknown"),
                        "service": port_info.get("name", "unknown"),
                        "version": port_info.get("version", ""),
                    })

            hosts.append(host_data)

        return {
            "hosts": hosts,
            "host_count": len(hosts),
            "scan_type": scan_type,
            "target": target,
            "command": nm.command_line(),
        }

    def xp_reward(self, result_data):
        """More XP for discovering more hosts."""
        host_count = result_data.get("host_count", 0)
        return 10 + host_count * 5

    def food_value(self, result_data):
        host_count = result_data.get("host_count", 0)
        return 5 + host_count * 3
