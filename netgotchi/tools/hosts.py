"""
netgotchi.tools.hosts
~~~~~~~~~~~~~~~~~~~~~
Discover SSH-able hosts from the user's system configuration.

LEARNING NOTES — this module teaches:
  - Reading and parsing config files (line-by-line text parsing)
  - os.path.expanduser() for home directory (~) expansion
  - Sets for deduplication
  - How /etc/hosts and ~/.ssh/config are structured

HOST SOURCES (checked in order):
  1. ~/.ssh/config  → "Host" directives (the gold standard)
  2. /etc/hosts     → IP-to-name mappings
  3. Fallback       → always includes 127.0.0.1

WHY THESE FILES?
    Network engineers maintain these files to track their infrastructure:
    - ~/.ssh/config: "Host myswitch" entries with IP, user, key, port
    - /etc/hosts: Local DNS overrides, often used for lab devices
    Both are plain text and safe to read (no secrets are exposed).
"""

import os
import re


def get_ssh_config_hosts():
    """Parse ~/.ssh/config for Host entries.

    LEARNING NOTE — SSH config format:
        ~/.ssh/config looks like this:

            Host myswitch
                HostName 192.168.1.10
                User admin
                Port 22

            Host webserver
                HostName 10.0.0.5
                User root

        We look for "Host" lines and grab both the alias and HostName.
        Wildcard entries (Host *) are skipped — they're defaults.

    Returns:
        List of dicts: [{"name": "myswitch", "host": "192.168.1.10",
                         "user": "admin", "port": 22}, ...]
    """
    config_path = os.path.expanduser("~/.ssh/config")
    if not os.path.exists(config_path):
        return []

    hosts = []
    current = None

    with open(config_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # LEARNING NOTE — case-insensitive matching:
            #   SSH config keywords are case-insensitive per spec.
            #   "Host", "host", "HOST" are all valid.
            key_value = line.split(None, 1)  # split on first whitespace
            if len(key_value) != 2:
                continue

            key, value = key_value
            key_lower = key.lower()

            if key_lower == "host":
                # Skip wildcard entries
                if "*" in value or "?" in value:
                    current = None
                    continue
                current = {"name": value, "host": value, "user": None, "port": 22}
                hosts.append(current)

            elif current is not None:
                if key_lower == "hostname":
                    current["host"] = value
                elif key_lower == "user":
                    current["user"] = value
                elif key_lower == "port":
                    try:
                        current["port"] = int(value)
                    except ValueError:
                        pass

    return hosts


def get_etc_hosts():
    """Parse /etc/hosts for non-localhost entries.

    LEARNING NOTE — /etc/hosts format:
        Each line is:  IP_ADDRESS  hostname [aliases...]

        Example:
            127.0.0.1   localhost
            192.168.1.1 gateway router.lan
            10.0.0.5    webserver

        We skip loopback (127.x, ::1) and link-local (fe80::, ff0x::)
        since those aren't useful SSH targets.

    Returns:
        List of dicts: [{"name": "gateway", "host": "192.168.1.1"}, ...]
    """
    hosts_path = "/etc/hosts"
    if not os.path.exists(hosts_path):
        return []

    hosts = []
    seen_ips = set()

    with open(hosts_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            ip = parts[0]

            # Skip loopback and link-local
            if (ip.startswith("127.") or ip == "::1"
                    or ip.startswith("fe80:") or ip.startswith("ff0")):
                continue

            if ip in seen_ips:
                continue
            seen_ips.add(ip)

            # Use the first hostname alias as the display name
            name = parts[1]
            hosts.append({"name": name, "host": ip, "user": None, "port": 22})

    return hosts


def discover_hosts():
    """Discover all SSH-able hosts from system config files.

    LEARNING NOTE — merging data sources:
        We collect hosts from multiple sources and deduplicate by IP.
        SSH config hosts come first (higher priority — user explicitly
        configured these). /etc/hosts fills in the rest.

    Returns:
        List of dicts, each with keys: name, host, user, port.
        Always includes 127.0.0.1 as a fallback.
    """
    all_hosts = []
    seen = set()

    # SSH config first (highest priority)
    for h in get_ssh_config_hosts():
        if h["host"] not in seen:
            seen.add(h["host"])
            all_hosts.append(h)

    # Then /etc/hosts
    for h in get_etc_hosts():
        if h["host"] not in seen:
            seen.add(h["host"])
            all_hosts.append(h)

    # Always have localhost as fallback
    if "127.0.0.1" not in seen:
        all_hosts.append({
            "name": "localhost",
            "host": "127.0.0.1",
            "user": None,
            "port": 22,
        })

    return all_hosts
