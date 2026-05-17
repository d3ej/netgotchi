package tools

import (
	"fmt"
	"io"
	"net"
	"os"
	"strings"
	"time"

	gossh "golang.org/x/crypto/ssh"
	"golang.org/x/crypto/ssh/agent"
)

// SSHParams holds the connection and auth details for an SSH session.
type SSHParams struct {
	Host       string
	Port       int
	Username   string
	AuthMethod string // "password" | "key" | "agent"
	Password   string
	KeyPath    string
}

// SSHShell wraps an active interactive SSH session.
type SSHShell struct {
	client  *gossh.Client
	session *gossh.Session
	stdin   io.WriteCloser
}

// Send writes a line to the remote shell's stdin.
func (s *SSHShell) Send(input string) error {
	_, err := io.WriteString(s.stdin, input)
	return err
}

// Close tears down the session and client.
func (s *SSHShell) Close() {
	if s.session != nil {
		_ = s.session.Close()
	}
	if s.client != nil {
		_ = s.client.Close()
	}
}

// RunSSHCommand opens a connection, executes one command, and returns the result.
func RunSSHCommand(params SSHParams, command string) ToolResult {
	start := time.Now()

	client, err := dialSSH(params)
	if err != nil {
		return ToolResult{
			ToolName: "ssh",
			Success:  false,
			Error:    err.Error(),
			Duration: time.Since(start).Seconds(),
			XPReward: 5,
		}
	}
	defer client.Close()

	sess, err := client.NewSession()
	if err != nil {
		return ToolResult{
			ToolName: "ssh",
			Success:  false,
			Error:    fmt.Sprintf("new session: %v", err),
			Duration: time.Since(start).Seconds(),
			XPReward: 5,
		}
	}
	defer sess.Close()

	outBytes, err := sess.CombinedOutput(command)
	duration := time.Since(start).Seconds()

	exitCode := 0
	if err != nil {
		if exitErr, ok := err.(*gossh.ExitError); ok {
			exitCode = exitErr.ExitStatus()
		}
	}

	return ToolResult{
		ToolName: "ssh",
		Success:  true,
		Data: map[string]any{
			"output":    string(outBytes),
			"exit_code": exitCode,
			"connected": true,
			"host":      params.Host,
			"command":   command,
		},
		Duration: duration,
		XPReward: 20,
	}
}

// OpenSSHShell connects and opens an interactive shell.
// Output is streamed into the returned channel; the channel is closed when the
// session ends.  The caller must read from the channel continuously.
func OpenSSHShell(params SSHParams) (*SSHShell, <-chan string, error) {
	client, err := dialSSH(params)
	if err != nil {
		return nil, nil, err
	}

	sess, err := client.NewSession()
	if err != nil {
		client.Close()
		return nil, nil, fmt.Errorf("new session: %w", err)
	}

	// Request a dumb PTY so the server sends plain text (no ANSI escape soup).
	modes := gossh.TerminalModes{
		gossh.ECHO:          0,
		gossh.TTY_OP_ISPEED: 14400,
		gossh.TTY_OP_OSPEED: 14400,
	}
	_ = sess.RequestPty("dumb", 24, 80, modes) // best-effort

	stdin, err := sess.StdinPipe()
	if err != nil {
		sess.Close()
		client.Close()
		return nil, nil, fmt.Errorf("stdin pipe: %w", err)
	}

	stdout, err := sess.StdoutPipe()
	if err != nil {
		sess.Close()
		client.Close()
		return nil, nil, fmt.Errorf("stdout pipe: %w", err)
	}

	if err := sess.Shell(); err != nil {
		sess.Close()
		client.Close()
		return nil, nil, fmt.Errorf("start shell: %w", err)
	}

	sh := &SSHShell{client: client, session: sess, stdin: stdin}
	ch := make(chan string, 64)

	go func() {
		defer close(ch)
		buf := make([]byte, 4096)
		for {
			n, err := stdout.Read(buf)
			if n > 0 {
				ch <- stripANSI(string(buf[:n]))
			}
			if err != nil {
				return
			}
		}
	}()

	return sh, ch, nil
}

// dialSSH establishes an authenticated SSH connection.
func dialSSH(params SSHParams) (*gossh.Client, error) {
	auth, err := buildAuth(params)
	if err != nil {
		return nil, err
	}

	cfg := &gossh.ClientConfig{
		User:            params.Username,
		Auth:            auth,
		HostKeyCallback: gossh.InsecureIgnoreHostKey(), //nolint:gosec
		Timeout:         10 * time.Second,
	}

	addr := fmt.Sprintf("%s:%d", params.Host, params.Port)
	return gossh.Dial("tcp", addr, cfg)
}

func buildAuth(params SSHParams) ([]gossh.AuthMethod, error) {
	switch params.AuthMethod {
	case "password":
		if params.Password == "" {
			return nil, fmt.Errorf("password auth selected but no password provided")
		}
		return []gossh.AuthMethod{gossh.Password(params.Password)}, nil

	case "key":
		keyPath := params.KeyPath
		if keyPath == "" {
			home, _ := os.UserHomeDir()
			keyPath = home + "/.ssh/id_rsa"
		}
		data, err := os.ReadFile(keyPath)
		if err != nil {
			return nil, fmt.Errorf("read key %s: %w", keyPath, err)
		}
		signer, err := gossh.ParsePrivateKey(data)
		if err != nil {
			return nil, fmt.Errorf("parse key: %w", err)
		}
		return []gossh.AuthMethod{gossh.PublicKeys(signer)}, nil

	default: // "agent" / auto
		var methods []gossh.AuthMethod
		if sock := os.Getenv("SSH_AUTH_SOCK"); sock != "" {
			conn, err := net.Dial("unix", sock)
			if err == nil {
				methods = append(methods, gossh.PublicKeysCallback(agent.NewClient(conn).Signers))
			}
		}
		// Also try common key files as fallback.
		home, _ := os.UserHomeDir()
		for _, name := range []string{"id_ed25519", "id_rsa", "id_ecdsa"} {
			data, err := os.ReadFile(home + "/.ssh/" + name)
			if err != nil {
				continue
			}
			if signer, err := gossh.ParsePrivateKey(data); err == nil {
				methods = append(methods, gossh.PublicKeys(signer))
			}
		}
		if len(methods) == 0 {
			return nil, fmt.Errorf("no SSH keys found; try password or key auth")
		}
		return methods, nil
	}
}

// stripANSI removes ANSI escape sequences from terminal output.
func stripANSI(s string) string {
	var out strings.Builder
	i := 0
	for i < len(s) {
		if s[i] == '\x1b' && i+1 < len(s) && s[i+1] == '[' {
			// Skip ESC [ ... letter
			i += 2
			for i < len(s) && (s[i] < 'A' || s[i] > 'Z') && (s[i] < 'a' || s[i] > 'z') {
				i++
			}
			i++ // skip the final letter
			continue
		}
		if s[i] == '\x1b' && i+1 < len(s) && s[i+1] == ']' {
			// Skip ESC ] ... BEL
			i += 2
			for i < len(s) && s[i] != '\x07' {
				i++
			}
			i++
			continue
		}
		out.WriteByte(s[i])
		i++
	}
	return out.String()
}
