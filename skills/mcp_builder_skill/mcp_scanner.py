import shutil
from pathlib import Path

# A simple map of common executables to a basic MCP tool template
COMMON_APPS = {
    "git": "git_status",
    "docker": "docker_ps",
    "npm": "npm_list",
}

TEMPLATE = """from mcp.server.fastmcp import FastMCP
import subprocess

mcp = FastMCP("{app_name}_mcp")

@mcp.tool()
def {tool_name}() -> str:
    \"\"\"Run basic {app_name} command.\"\"\"
    try:
        result = subprocess.run(["{app_name}", "{arg}"], capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        return f"Error running {app_name}: {{e}}"

if __name__ == "__main__":
    mcp.run()
"""

def scan_and_generate():
    output_dir = Path("mcp_servers")
    output_dir.mkdir(exist_ok=True)
    print("Scanning system for common apps...")

    found_apps = []
    for app in COMMON_APPS:
        if shutil.which(app):
            found_apps.append(app)

    if not found_apps:
        print("No supported apps found for auto-generation.")
        return

    print(f"Found apps: {', '.join(found_apps)}")
    for app in found_apps:
        if app == "git":
            arg = "status"
        elif app == "docker":
            arg = "ps"
        elif app == "npm":
            arg = "list"
        else:
            arg = "--version"

        tool_name = COMMON_APPS[app]
        code = TEMPLATE.format(app_name=app, tool_name=tool_name, arg=arg)

        server_path = output_dir / f"{app}_server.py"
        with open(server_path, "w") as f:
            f.write(code)
        print(f"Generated MCP server for {app} -> {server_path}")

if __name__ == "__main__":
    scan_and_generate()
