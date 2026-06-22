import subprocess
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False
)
mcp = FastMCP("My Test Server", transport_security=security)

# --- CONFIGURATION FOR THE WEAK PC ---
REMOTE_USER = ""      # e.g., 'pi' or 'john'
REMOTE_HOST = "10.129.28.190"       # The IP address of the weaker PC

@mcp.tool()
def list_directory(path: str = ".") -> str:
    """Run the 'ls' command to list the contents of a directory on the weak PC."""
    try:
        # Construct the SSH command
        # This translates to: ssh user@ip "ls -l /path"
        ssh_command = ["ssh", f"{REMOTE_USER}@{REMOTE_HOST}", "ls", "-l", path]
        
        result = subprocess.run(
            ssh_command, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error executing remote ls on {path}: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

if __name__ == "__main__":
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8000
    mcp.run(transport='sse')
