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
import threading
import time

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
        pkey_path = params.get("pkey_path") or key_path
        password = params.get("password")
        allow_agent = params.get("allow_agent", True)
        look_for_keys = params.get("look_for_keys", True)
        keyboard_interactive = params.get("keyboard_interactive", False)

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
            #   password: SSH password (for password/kbi auth)
            #   key_filename: path to your private key file
            #   timeout: seconds to wait for connection
            #   allow_agent: try SSH agent for keys
            #   look_for_keys: auto-find keys in ~/.ssh/
            #   auth_timeout: timeout for authentication
            connect_kwargs = {
                "hostname": host,
                "port": port,
                "username": username,
                "timeout": 10,
                "auth_timeout": 10,
                "banner_timeout": 10,
                "allow_agent": allow_agent,
                "look_for_keys": look_for_keys,
            }

            if keyboard_interactive:
                # Prefer keyboard-interactive with password provided
                connect_kwargs["allow_agent"] = False
                connect_kwargs["look_for_keys"] = False
                if password:
                    connect_kwargs["password"] = password

            elif password:
                connect_kwargs["password"] = password

            if pkey_path:
                connect_kwargs["key_filename"] = pkey_path

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

    def open_shell(self, params, on_output, on_close=None):
        """Open an interactive SSH shell and stream output through callbacks."""
        if not HAS_PARAMIKO:
            on_output("paramiko not installed! Run: pip install paramiko\n")
            if on_close:
                on_close(False, "paramiko missing")
            return None

        host = params.get("host", "127.0.0.1")
        port = params.get("port", 22)
        username = params.get("username", os.getenv("USER", "admin"))
        key_path = params.get("key_path")
        pkey_path = params.get("pkey_path") or key_path
        password = params.get("password")
        allow_agent = params.get("allow_agent", True)
        look_for_keys = params.get("look_for_keys", True)
        keyboard_interactive = params.get("keyboard_interactive", False)

        stop_event = threading.Event()

        session = {
            "client": None,
            "channel": None,
            "stop_event": stop_event,
        }

        def worker():
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            session["client"] = client

            try:
                connect_kwargs = {
                    "hostname": host,
                    "port": port,
                    "username": username,
                    "timeout": 10,
                    "auth_timeout": 10,
                    "banner_timeout": 10,
                    "allow_agent": allow_agent,
                    "look_for_keys": look_for_keys,
                }

                if keyboard_interactive:
                    connect_kwargs["allow_agent"] = False
                    connect_kwargs["look_for_keys"] = False
                    if password:
                        connect_kwargs["password"] = password
                elif password:
                    connect_kwargs["password"] = password

                if pkey_path:
                    connect_kwargs["key_filename"] = pkey_path

                client.connect(**connect_kwargs)

                channel = client.invoke_shell(term="xterm", width=80, height=24)
                channel.settimeout(0.1)
                session["channel"] = channel

                on_output(f"*** Connected to {host} as {username} ***\n")

                while not stop_event.is_set() and channel.active and not channel.closed:
                    if channel.recv_ready():
                        chunk = channel.recv(1024).decode("utf-8", errors="replace")
                        on_output(chunk)
                    else:
                        time.sleep(0.05)

                on_output("*** SSH session closed ***\n")
                if on_close:
                    on_close(True, None)

            except Exception as e:
                on_output(f"SSH error: {e}\n")
                if on_close:
                    on_close(False, str(e))

            finally:
                if session.get("channel") is not None:
                    try:
                        session["channel"].close()
                    except Exception:
                        pass
                if session.get("client") is not None:
                    try:
                        session["client"].close()
                    except Exception:
                        pass

        threading.Thread(target=worker, daemon=True).start()

        def send_command(line):
            ch = session.get("channel")
            if ch and ch.active and not ch.closed:
                try:
                    ch.send(line)
                    return True
                except Exception:
                    return False
            return False

        def close_session():
            stop_event.set()
            ch = session.get("channel")
            if ch is not None:
                try:
                    ch.close()
                except Exception:
                    pass
            cli = session.get("client")
            if cli is not None:
                try:
                    cli.close()
                except Exception:
                    pass

        session["send"] = send_command
        session["close"] = close_session

        return session

    def xp_reward(self, result_data):
        if result_data.get("connected"):
            return 20  # SSH is a "big" action
        return 5

    def food_value(self, result_data):
        if result_data.get("connected"):
            return 12
        return 2
