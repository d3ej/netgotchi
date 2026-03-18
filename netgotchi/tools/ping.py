"""
netgotchi.tools.ping
~~~~~~~~~~~~~~~~~~~~
ICMP Ping tool — the most fundamental network diagnostic.

LEARNING NOTES — this module teaches:
  - subprocess module (running system commands from Python)
  - Regular expressions (parsing structured text output)
  - Platform-specific code (Linux vs Windows differences)
  - Error handling patterns (try/except with specific exceptions)

WHAT IS PING?
    Ping sends an ICMP Echo Request packet to a target host and waits
    for an ICMP Echo Reply. It measures:
    - Whether the host is reachable (did we get a reply?)
    - Round-trip time (RTT) — how long the reply took in milliseconds
    - Packet loss — what % of packets got no reply

    It's the "hello, are you there?" of networking. Named after sonar.

WHY SUBPROCESS INSTEAD OF SCAPY?
    We use subprocess to call the system's `ping` command because:
    1. It doesn't require root/sudo (raw sockets do)
    2. It's simpler for our first tool
    3. It works exactly like typing `ping` in your terminal

    Later we can add a scapy-based ping that gives more control but
    needs elevated privileges.
"""

import subprocess
import re
import platform

from .base import BaseTool


class PingTool(BaseTool):
    """ICMP Ping tool using system ping command.

    Usage:
        ping = PingTool()
        ping.run(
            {"target": "8.8.8.8", "count": 4},
            callback=handle_result
        )
    """

    @property
    def name(self):
        return "Ping"

    def _execute(self, params):
        """Run ping and parse the results.

        LEARNING NOTE — subprocess.run():
            subprocess.run() launches an external program and waits for
            it to finish. Key arguments:
              - capture_output=True: Capture stdout/stderr as strings
              - text=True: Return strings instead of bytes
              - timeout: Kill the process if it takes too long

            The result has:
              - .stdout: The command's standard output
              - .stderr: Error output
              - .returncode: 0 = success, non-zero = failure

        Args:
            params: Dict with:
                target (str): IP or hostname to ping.
                count (int): Number of pings to send (default 4).

        Returns:
            Dict with parsed results.
        """
        target = params.get("target", "127.0.0.1")
        count = params.get("count", 4)

        # Build the command — differs by platform
        # LEARNING NOTE — platform detection:
        #   platform.system() returns 'Linux', 'Darwin' (macOS), or 'Windows'.
        #   Linux/Mac use -c for count, Windows uses -n.
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", str(count), target]
        else:
            cmd = ["ping", "-c", str(count), target]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=count * 5 + 5  # generous timeout
            )

            return self._parse_output(result.stdout, result.returncode)

        except subprocess.TimeoutExpired:
            return {
                "reachable": False,
                "rtt_avg": None,
                "rtt_min": None,
                "rtt_max": None,
                "packet_loss": 100.0,
                "raw_output": "Ping timed out",
                "target": target,
            }

    def _parse_output(self, output, returncode):
        """Parse ping command output to extract RTT and packet loss.

        LEARNING NOTE — regular expressions (regex):
            re.search(pattern, string) looks for a pattern in text.
            Patterns use special syntax:
              \\d+     = one or more digits
              \\.      = literal dot
              (...)   = capture group (extract the matched text)
              [\\d.]+  = one or more digits or dots

            Example: re.search(r'(\\d+)% packet loss', text)
            Matches "25% packet loss" and captures "25" in group(1).

            Regex is ESSENTIAL for network engineering — parsing command
            output, log files, config files, etc.

        Args:
            output: Raw stdout string from ping command.
            returncode: Process exit code.

        Returns:
            Dict of parsed results.
        """
        result = {
            "reachable": returncode == 0,
            "rtt_avg": None,
            "rtt_min": None,
            "rtt_max": None,
            "packet_loss": 100.0,
            "raw_output": output,
        }

        # Parse packet loss: "X% packet loss"
        loss_match = re.search(r'(\d+(?:\.\d+)?)% packet loss', output)
        if loss_match:
            result["packet_loss"] = float(loss_match.group(1))

        # Parse RTT stats: "rtt min/avg/max/mdev = X/X/X/X ms"
        # LEARNING NOTE — regex alternation:
        #   (rtt|round-trip) matches either "rtt" or "round-trip"
        #   This handles different ping output formats.
        rtt_match = re.search(
            r'(?:rtt|round-trip).+?=\s*([\d.]+)/([\d.]+)/([\d.]+)',
            output
        )
        if rtt_match:
            result["rtt_min"] = float(rtt_match.group(1))
            result["rtt_avg"] = float(rtt_match.group(2))
            result["rtt_max"] = float(rtt_match.group(3))

        return result

    def xp_reward(self, result_data):
        """More XP for successful pings with good RTT."""
        if result_data.get("reachable"):
            rtt = result_data.get("rtt_avg", 100)
            if rtt and rtt < 10:
                return 15  # Fast ping bonus
            return 10
        return 5  # Still get some XP for trying

    def food_value(self, result_data):
        if result_data.get("reachable"):
            return 8
        return 2
