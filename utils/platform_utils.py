import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Optional, List, Union


def get_platform() -> str:
    """Get the current platform (windows, linux, darwin)"""
    return platform.system().lower()


def is_windows() -> bool:
    """Check if running on Windows"""
    return get_platform() == "windows"


def is_linux() -> bool:
    """Check if running on Linux"""
    return get_platform() == "linux"


def is_macos() -> bool:
    """Check if running on macOS"""
    return get_platform() == "darwin"


def get_secrets_dir() -> str:
    """Get platform-appropriate secrets directory"""
    if is_windows():
        return os.path.join(os.getenv('APPDATA', ''), 'autonomous-agent', 'secrets')
    else:
        return '/run/secrets'


def get_home_dir() -> str:
    """Get platform-appropriate home directory"""
    return str(Path.home())


def get_repo_dir() -> str:
    """Get platform-appropriate repository directory"""
    if is_windows():
        return os.path.join(get_home_dir(), 'repos', 'Autonomous-Agent')
    else:
        return '/home/ubuntu/repos/Autonomous-Agent'


def normalize_path(path: Union[str, Path]) -> str:
    """Normalize path for current platform"""
    return str(Path(path).resolve())


def run_command(cmd: Union[str, List[str]], shell: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """Run command with platform-appropriate shell"""
    if isinstance(cmd, str):
        if is_windows():
            cmd = ['powershell', '-Command', cmd]
            shell = False
        else:
            shell = True
    
    print(f"▶️ {cmd}")
    return subprocess.run(cmd, shell=shell, check=check, capture_output=True, text=True)


def get_ffmpeg_command() -> str:
    """Get platform-appropriate FFmpeg command"""
    if is_windows():
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return 'ffmpeg'
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg:\n"
                "1. Download from https://ffmpeg.org/download.html#build-windows\n"
                "2. Add to PATH environment variable\n"
                "3. Or use: winget install FFmpeg"
            )
    else:
        return 'ffmpeg'


def get_terraform_command() -> str:
    """Get platform-appropriate Terraform command"""
    if is_windows():
        try:
            subprocess.run(['terraform', '--version'], capture_output=True, check=True)
            return 'terraform'
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "Terraform not found. Please install Terraform:\n"
                "1. Download from https://www.terraform.io/downloads\n"
                "2. Add to PATH environment variable\n"
                "3. Or use: winget install HashiCorp.Terraform"
            )
    else:
        return 'terraform'


def get_tor_config() -> dict:
    """Get platform-appropriate Tor configuration"""
    if is_windows():
        return {
            'control_port': 9051,
            'config_file': os.path.join(os.getenv('APPDATA', ''), 'tor', 'torrc'),
            'service_name': 'tor',
            'install_instructions': (
                "Install Tor Browser or Tor service:\n"
                "1. Download from https://www.torproject.org/download/\n"
                "2. Or use: winget install TorProject.TorBrowser\n"
                "3. Configure control port in torrc file"
            )
        }
    else:
        return {
            'control_port': 9051,
            'config_file': '/etc/tor/torrc',
            'service_name': 'tor',
            'install_instructions': (
                "Install Tor:\n"
                "Ubuntu/Debian: sudo apt install tor\n"
                "macOS: brew install tor"
            )
        }


def ensure_directory(path: Union[str, Path]) -> str:
    """Ensure directory exists, create if necessary"""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return str(path_obj)


def get_python_executable() -> str:
    """Get the current Python executable path"""
    return sys.executable


def get_package_install_command(package: str) -> List[str]:
    """Get platform-appropriate package installation command"""
    python_exe = get_python_executable()
    return [python_exe, '-m', 'pip', 'install', package]


def check_dependency(command: str, install_instructions: str = "") -> bool:
    """Check if a system dependency is available"""
    try:
        subprocess.run([command, '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        if install_instructions:
            print(f"⚠️ {command} not found. {install_instructions}")
        return False


def get_shell_command_separator() -> str:
    """Get platform-appropriate command separator for shell commands"""
    if is_windows():
        return '; '  # PowerShell uses semicolon
    else:
        return ' && '  # Bash uses &&


def format_shell_command(commands: List[str]) -> str:
    """Format multiple commands for platform-appropriate shell execution"""
    separator = get_shell_command_separator()
    return separator.join(commands)
