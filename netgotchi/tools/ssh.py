"""
netgotchi.tools.ssh
~~~~~~~~~~~~~~~~~~~
SSH client tool using paramiko — connect to network devices!

LEARNING NOTES — this module teaches:
  - The paramiko library (Python SSH implementation)
  - SSH key-based authentication (why it's better than passwords)
  - Context managers (with statement for clean resource handling)
  - How network engineers SSH into routers/switches programmatically

WHAT IS PARAMIKO?
    Paramiko is a pure-Python implementation of the SSH v2 protocol.
    It lets you:
    - Connect to remote devices (routers, switches, servers)
    - Execute commands and read the output
    - Transfer files (SFTP)
    - All from Python code!

    Network engineers use this constantly to automate device management.
    Instead of manually SSH-ing into 50 switches to check status,
    you write a Python script that does it for you.

SSH AUTHENTICATION:
    We use key-based auth (not passwords) because:
    1. It's more secure (keys are much harder to brute-force)
    2. It's automatable (no typing passwords)
    3. It's the standard for network automation

    Your SSH keys live in ~/.ssh/id_rsa (private) and ~/.ssh/id_rsa.pub (public).
"""

import os

from .base import BaseTool

# Paramiko is an optional dependency — handle gracefully if missing
try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False


class SSHTool(BaseTool):
    """SSH into devices and run commands.

    Usage:
        ssh = SSHTool()
        ssh.run({
            "host": "192.168.1.1",
            "username": "admin",
            "command": "show version",
        }, callback=handle_result)
    """

    @property
    def name(self):
        return "SSH"

    def _execute(self, params):
        """Connect via SSH and execute a command.

        LEARNING NOTE — paramiko workflow:
            1. Create SSHClient object
            2. Set host key policy (how to handle unknown hosts)
            3. Connect with credentials
            4. Execute command → returns (stdin, stdout, stderr) streams
            5. Read output from stdout
            6. Close the connection

        SECURITY NOTE — host key policy:
            AutoAddPolicy automatically trusts unknown hosts. This is
            convenient for lab environments but INSECURE for production.
            In production, use RejectPolicy and manage known_hosts.
            For our network lab (containerlab), AutoAdd is fine.

        Args:
            params: Dict with:
                host (str): IP or hostname.
                port (int): SSH port (default 22).
                username (str): Login username.
                command (str): Command to execute.
                key_path (str): Path to SSH private key (optional).

        Returns:
            Dict with command output.
        """
        if not HAS_PARAMIKO:
            return {
                "output": "paramiko not installed! Run: pip install paramiko",
                "exit_code": -1,
                "connected": False,
            }

        host = params.get("host", "127.0.0.1")
        port = params.get("port", 22)
        username = params.get("username", os.getenv("USER", "admin"))
        command = params.get("command", "whoami")
        key_path = params.get("key_path")

        # LEARNING NOTE — paramiko.SSHClient():
        #   This is the main class you'll use. It wraps the entire
        #   SSH connection lifecycle.
        client = paramiko.SSHClient()

        # Accept unknown host keys (fine for labs, not for production)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # LEARNING NOTE — connect() arguments:
            #   hostname: IP or DNS name
            #   port: default 22
            #   username: login account
            #   key_filename: path to your private key file
            #   timeout: seconds to wait for connection
            #   allow_agent: try SSH agent for keys
            #   look_for_keys: auto-find keys in ~/.ssh/
            connect_kwargs = {
                "hostname": host,
                "port": port,
                "username": username,
                "timeout": 10,
                "allow_agent": True,
                "look_for_keys": True,
            }

            if key_path:
                connect_kwargs["key_filename"] = key_path

            client.connect(**connect_kwargs)

            # LEARNING NOTE — exec_command():
            #   Returns 3 file-like objects: stdin, stdout, stderr.
            #   stdout.read() gives you the command output as bytes.
            #   .decode() converts bytes → string.
            #
            #   This is how Ansible, Netmiko, and other network
            #   automation tools work under the hood!
            stdin, stdout, stderr = client.exec_command(command)

            output = stdout.read().decode("utf-8", errors="replace")
            errors = stderr.read().decode("utf-8", errors="replace")
            exit_code = stdout.channel.recv_exit_status()

            return {
                "output": output,
                "errors": errors,
                "exit_code": exit_code,
                "connected": True,
                "host": host,
                "command": command,
            }

        except paramiko.AuthenticationException:
            return {
                "output": f"Authentication failed for {username}@{host}",
                "exit_code": -1,
                "connected": False,
                "host": host,
            }
        except paramiko.SSHException as e:
            return {
                "output": f"SSH error: {e}",
                "exit_code": -1,
                "connected": False,
                "host": host,
            }
        except OSError as e:
            return {
                "output": f"Connection failed: {e}",
                "exit_code": -1,
                "connected": False,
                "host": host,
            }
        finally:
            # LEARNING NOTE — finally:
            #   The finally block ALWAYS runs, even if an exception occurred.
            #   This ensures we close the connection and don't leak resources.
            #   This is similar to how you free SDL resources in your C project.
            client.close()

    def xp_reward(self, result_data):
        if result_data.get("connected"):
            return 20  # SSH is a "big" action
        return 5

    def food_value(self, result_data):
        if result_data.get("connected"):
            return 12
        return 2
