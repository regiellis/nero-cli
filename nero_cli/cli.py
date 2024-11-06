#!/usr/bin/env python3

"""
MIT License

Copyright (c) 2024 itsjustregi (Regi E. regi@bynine.io)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# usage: nero [-h] [--dry-run] [--download-only] [--latest] [--version VERSION] [--rollback] [--keep] [--download-dir DOWNLOAD_DIR] [--check] [--update-config]

# Invoke Installer Script

# options:
#   -h, --help            show this help message and exit
#   --dry-run             Perform a dry run without making any changes
#   --download-only       Only download the installer without running it
#   --latest              Check for the latest version and prompt for update
#   --version VERSION     Specify a version to download and install
#   --rollback            Rollback to the previous version
#   --keep                Keep the downloaded file after installation
#   --download-dir DOWNLOAD_DIR
#                         Specify the directory to save downloads
#   --check               Display current configuration and check for updates
#   --list-versions       List available versions of InvokeAI
#   --update-config       Only update the configuration file with the current or specified version

import os
import json
import subprocess
import argparse
import tempfile
import shutil
import sys
import platform
import time
import urllib.request
from pathlib import Path
from datetime import datetime
from packaging import version


from typing import Dict, Any, Optional, Tuple


# TODO: TONS of refactoring needed here. This is a mess.


# ANCHOR: ANSI color codes
class Colors:
    HEADER = "\033[33m"
    OKBLUE = "\033[36m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# ANCHOR: Configuration
def get_config_dir() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ["APPDATA"]) / "itsjustregi" / "nero"
    elif platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "itsjustregi" / "nero"
    else:
        return Path.home() / ".config" / "itsjustregi" / "nero"


SCRIPT_NAME: str = "nero"
CONFIG_DIR: Path = get_config_dir()
CONFIG_FILE: Path = CONFIG_DIR / f"{SCRIPT_NAME}.json"
MIN_PYTHON_VERSION: Tuple[int, int, int] = (3, 10, 1)
MAX_PYTHON_VERSION: Tuple[int, int, int] = (3, 11, 9)
TEMP_ENV: str = (
    "nero-env"  # TEMP_ENV is used for pyenv to create a temporary environment for installation
)


# ANCHOR: Helper Functions
def print_step(message: str) -> None:
    print(f"\n{Colors.HEADER}/// {message} ///{Colors.ENDC}")


def check_python_version() -> bool:
    current_version = sys.version_info[:3]
    if MIN_PYTHON_VERSION <= current_version <= MAX_PYTHON_VERSION:
        print_step(f"Using Python {'.'.join(map(str, current_version))}")
        return True
    return False


def check_command(command: str) -> bool:
    return shutil.which(command) is not None


def run_command(command: str, dry_run: bool = False, wait: bool = False) -> None:
    if dry_run:
        print(
            f"{Colors.WARNING}{'[DRY RUN] Would run and wait:' if wait else '[DRY RUN] Would run:'}{command}{Colors.ENDC}"
        )
    else:
        print(
            f"{Colors.OKBLUE}{'Executing and waiting:' if wait else 'Executing:'}{command}{Colors.ENDC}"
        )

        if not wait:
            subprocess.run(command, shell=True, check=True)
        else:
            process = subprocess.Popen(command, shell=True)
            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command)


# ANCHOR: Version Management
def get_latest_version() -> str:
    print_step("Checking for the latest version")
    url = "https://api.github.com/repos/invoke-ai/InvokeAI/releases/latest"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
    return data["tag_name"].lstrip("v")


def get_versions():
    print_step("Fetching InvokeAI versions")
    url = "https://api.github.com/repos/invoke-ai/InvokeAI/releases"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())

    versions = {"latest": None, "previous": [], "pre_release": []}

    for release in data:
        ver = release["tag_name"].lstrip("v")
        if release["prerelease"]:
            versions["pre_release"].append(ver)
        elif not versions["latest"]:
            versions["latest"] = ver
        else:
            versions["previous"].append(ver)

    # Sort versions
    versions["previous"].sort(key=lambda x: version.parse(x), reverse=True)
    versions["pre_release"].sort(key=lambda x: version.parse(x), reverse=True)

    return versions


def display_versions() -> None:
    versions = get_versions()

    print(f"\n{Colors.BOLD}{Colors.UNDERLINE}InvokeAI Versions:{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Latest: {versions['latest']}{Colors.ENDC}")

    print(f"\n{Colors.BOLD}Previous Releases:{Colors.ENDC}")
    for ver in versions["previous"][:5]:  # Display top 5 previous versions
        print(f"{Colors.OKBLUE}- {ver}{Colors.ENDC}")

    print(f"\n{Colors.BOLD}Pre-release Versions:{Colors.ENDC}")
    for ver in versions["pre_release"][:3]:  # Display top 3 pre-release versions
        print(f"{Colors.WARNING}- {ver}{Colors.ENDC}")


def download_version(version: str):
    base_url = "https://github.com/invoke-ai/InvokeAI/releases/download"
    filename = f"InvokeAI-installer-v{version}.zip"
    url = f"{base_url}/v{version}/{filename}"

    download_dir = Path.home() / "Downloads"  # Default to user's Downloads directory
    full_path = download_dir / filename

    try:
        download_file(url, full_path)
        print(
            f"{Colors.OKGREEN}Successfully downloaded version {version} to {full_path}{Colors.ENDC}"
        )
    except Exception as e:
        print(
            f"{Colors.FAIL}Failed to download version {version}. Error: {str(e)}{Colors.ENDC}"
        )


def download_file(url: str, filename: Path, dry_run: bool = False) -> None:
    if dry_run:
        print(
            f"{Colors.WARNING}[DRY RUN] Would download: {url} to {filename}{Colors.ENDC}"
        )
    else:
        print(f"{Colors.OKBLUE}Downloading: {url} to {filename}{Colors.ENDC}")
        urllib.request.urlretrieve(url, filename)
        print(f"{Colors.OKGREEN}Download completed{Colors.ENDC}")


# ANCHOR: Configuration Management
def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
        "current_version": None,
        "previous_version": None,
        "last_update": None,
    }


def save_config(config: Dict[str, Any], dry_run: bool = False) -> None:
    if dry_run:
        print(f"{Colors.WARNING}[DRY RUN] Would save config: {config}{Colors.ENDC}")
    else:
        print(f"{Colors.OKBLUE}Saving configuration{Colors.ENDC}")
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)


def update_config(
    version: str, dry_run: bool = False, update_only: bool = False
) -> None:
    config = load_config()
    config["previous_version"] = config["current_version"]
    config["current_version"] = version
    config["last_update"] = datetime.now().isoformat()
    save_config(config, dry_run)
    if update_only:
        print_step(f"{Colors.OKGREEN}Configuration updated successfully{Colors.ENDC}")


def prompt_user(question: str) -> bool:
    return input(f"{Colors.BOLD}{question} (y/n): {Colors.ENDC}").lower().strip() == "y"


def get_temp_dir() -> Path:
    return Path(tempfile.gettempdir())


def check_directory_permissions(directory: Path) -> bool:
    return os.access(directory, os.W_OK)


def cleanup(zip_path: Optional[Path], keep: bool) -> None:
    print_step("Cleaning up")
    if zip_path and not keep and zip_path.exists():
        for attempt in range(5):  # Try up to 5 times
            try:
                os.remove(zip_path)
                print(f"{Colors.OKGREEN}Successfully removed {zip_path}{Colors.ENDC}")
                break
            except PermissionError:
                print(
                    f"{Colors.WARNING}Unable to remove file, retrying in 1 second...{Colors.ENDC}"
                )
                time.sleep(1)
        else:
            print(
                f"{Colors.FAIL}Failed to remove {zip_path} after multiple attempts{Colors.ENDC}"
            )

    temp_dir = Path(tempfile.gettempdir()) / "InvokeAI-Installer"
    if temp_dir.exists():
        for attempt in range(5):  # Try up to 5 times
            try:
                shutil.rmtree(temp_dir)
                print(
                    f"{Colors.OKGREEN}Successfully removed temporary directory{Colors.ENDC}"
                )
                break
            except PermissionError:
                print(
                    f"{Colors.WARNING}Unable to remove temporary directory, retrying in 1 second...{Colors.ENDC}"
                )
                time.sleep(1)
        else:
            print(
                f"{Colors.FAIL}Failed to remove temporary directory after multiple attempts{Colors.ENDC}"
            )


def get_rollback_version(config: Dict[str, Any]) -> str:
    previous_version = config.get("previous_version")
    if previous_version:
        return previous_version
    else:
        while True:
            entered_version = input(
                f"{Colors.BOLD}Enter the version you want to rollback to: {Colors.ENDC}"
            ).strip()
            if entered_version:
                return entered_version
            else:
                print(f"{Colors.WARNING}Please enter a valid version.{Colors.ENDC}")


def check_and_display_config(config: Dict[str, Any]) -> Optional[str]:
    print_step("Current Configuration")
    for key, value in config.items():
        print(f"{Colors.BOLD}{key}:{Colors.ENDC} {value}")

    current_version = config.get("current_version")
    latest_version = get_latest_version()

    if current_version:
        print(f"\n{Colors.BOLD}Current version:{Colors.ENDC} {current_version}")
        print(f"{Colors.BOLD}Latest version available:{Colors.ENDC} {latest_version}")

        if current_version != latest_version:
            choice = (
                input(
                    f"{Colors.BOLD}Do you want to upgrade (u), downgrade (d), or cancel (c)? {Colors.ENDC}"
                )
                .strip()
                .lower()
            )
            if choice == "u":
                return latest_version
            elif choice == "d":
                downgrade_version = input(
                    f"{Colors.BOLD}Enter the version you want to downgrade to (or leave blank to cancel): {Colors.ENDC}"
                ).strip()
                return downgrade_version if downgrade_version else None
            else:
                return None
        else:
            print(
                f"{Colors.OKGREEN}You have the latest version installed.{Colors.ENDC}"
            )
            return None
    else:
        print(f"\n{Colors.WARNING}No version currently installed.{Colors.ENDC}")
        return (
            latest_version
            if prompt_user(
                "No current version found. Do you want to install the latest version?"
            )
            else None
        )


def check_for_updates(current_version: str) -> Optional[str]:
    latest_version = get_latest_version()
    if current_version:
        print_step(
            f"Current version: {current_version}, Latest version available: {latest_version}"
        )
        if current_version != latest_version:
            choice = (
                input(
                    f"{Colors.BOLD}Do you want to upgrade (u), downgrade (d), or cancel (c)? {Colors.ENDC}"
                )
                .strip()
                .lower()
            )
            if choice == "u":
                return latest_version
            elif choice == "d":
                downgrade_version = input(
                    f"{Colors.BOLD}Enter the version you want to downgrade to (or leave blank to cancel): {Colors.ENDC}"
                ).strip()
                return downgrade_version if downgrade_version else None
        print(f"{Colors.OKGREEN}You have the latest version installed.{Colors.ENDC}")
        return None
    else:
        print(f"\n{Colors.WARNING}No version currently installed.{Colors.ENDC}")
        return (
            latest_version
            if prompt_user(
                "No current version found. Do you want to install the latest version?"
            )
            else None
        )


# ANCHOR: Environment Handling
def load_shell_environment():
    system_platform = platform.system()
    if system_platform in ["Windows", "Darwin"]:
        # For Windows and MacOS, we directly use the existing environment.
        pass
    else:
        # Unix/Linux systems
        user_shell = os.environ.get("SHELL", "/bin/bash")
        shell_command = (
            "env -i bash -ic 'env'" if "bash" in user_shell else "env -i zsh -ic 'env'"
        )
        try:
            output = subprocess.check_output(
                shell_command, shell=True, text=True, stderr=subprocess.DEVNULL
            )
            for line in output.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value
        except subprocess.CalledProcessError:
            print(
                "Warning: Failed to load shell environment. Using current environment."
            )


# TODO: Fix pyenv activation, this is hacky and not working as expected (Removed for now)
# def env_global_pyenv_fix() -> None:
#     load_shell_environment()
#     run_command(f"pyenv activate {TEMP_ENV}", args.dry_run)
#     run_command(
#         f"pyenv global {MAX_PYTHON_VERSION[0]}.{MAX_PYTHON_VERSION[1]}.{MAX_PYTHON_VERSION[2]}",
#         args.dry_run,
#     )
#     run_command(f"pyenv deactivate {TEMP_ENV}", args.dry_run)


# ANCHOR: Main Function
def nero(args: argparse.Namespace) -> None:
    print_step("Starting Invoke Installer")
    zip_path = None

    try:
        load_shell_environment()
        python_ok = check_python_version()

        # if not python_ok and args.use_pyenv:
        #     print_step("Attempting to use pyenv for installation.")
        #     if not check_command("pyenv"):
        #         print(
        #             f"{Colors.FAIL}Error: pyenv is not installed. Please install it first.{Colors.ENDC}"
        #         )
        #         return

        #     if (
        #         run_command("pyenv version-name", args.dry_run)
        #         == f"{MAX_PYTHON_VERSION[0]}.{MAX_PYTHON_VERSION[1]}.{MAX_PYTHON_VERSION[2]}"
        #     ):
        #         run_command(
        #             f"pyenv install {MAX_PYTHON_VERSION[0]}.{MAX_PYTHON_VERSION[1]}.{MAX_PYTHON_VERSION[2]}",
        #             args.dry_run,
        #         )
        #         env_global_pyenv_fix()
        #     else:
        #         env_global_pyenv_fix()

        #     python_ok = check_python_version()

        if not python_ok:
            if not args.use_pyenv:
                print(
                    f"{Colors.FAIL}Error: Python version {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}.{MIN_PYTHON_VERSION[2]} - {MAX_PYTHON_VERSION[0]}.{MAX_PYTHON_VERSION[1]}.{MAX_PYTHON_VERSION[2]} is required.{Colors.ENDC}"
                )
                print(
                    "Please install an appropriate Python version 3.10.1 - 3.11.9 "  # or use --use-pyenv to attempt installation with pyenv."
                )
            else:
                print(
                    f"{Colors.FAIL}Error: Even with pyenv set up, an appropriate Python version could not be found.{Colors.ENDC}"
                )
            return

        config = load_config()

        if args.check:
            action_result = check_and_display_config(config)
            if action_result is None:
                print(f"{Colors.WARNING}No action taken. Exiting.{Colors.ENDC}")
                return
            args.version = action_result

        if args.rollback:
            args.version = get_rollback_version(config)

        if args.list_versions:
            display_versions()
            return

        if not args.version:
            action_result = check_for_updates(config.get("current_version", ""))
            if action_result is None or action_result == "":
                return
            args.version = action_result

        if args.update_config:
            update_config(
                args.version or get_latest_version(), args.dry_run, update_only=True
            )
            return

        zip_filename = f"InvokeAI-installer-v{args.version}.zip"
        download_url = f"https://github.com/invoke-ai/InvokeAI/releases/download/v{args.version}/{zip_filename}"
        download_dir = Path(args.download_dir) if args.download_dir else get_temp_dir()

        if not check_directory_permissions(download_dir):
            print(
                f"{Colors.FAIL}Error: No write permission for directory {download_dir}{Colors.ENDC}"
            )
            return

        zip_path = download_dir / zip_filename
        print_step(f"Downloading InvokeAI version {args.version}")
        download_file(download_url, zip_path, args.dry_run)

        if args.download_only:
            print(f"{Colors.OKGREEN}File saved to: {zip_path}{Colors.ENDC}")
            return

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            print_step("Extracting the installer")

            if platform.system() == "Windows":
                run_command(
                    f"powershell -command Expand-Archive -Path {zip_path} -DestinationPath {temp_dir_path}",
                    args.dry_run,
                )
            else:
                run_command(f"unzip -o {zip_path} -d {temp_dir_path}", args.dry_run)

            installer_dir = temp_dir_path / "InvokeAI-Installer"
            if not args.dry_run:
                os.chdir(installer_dir)

            print_step("Running the installer")
            if platform.system() == "Windows":
                run_command("install.bat", args.dry_run)
            else:
                run_command("./install.sh", args.dry_run)

        update_config(args.version, args.dry_run)
        print_step(f"{Colors.OKGREEN}Installation completed successfully{Colors.ENDC}")

    except Exception as e:
        print(f"{Colors.FAIL}An error occurred: {e}{Colors.ENDC}")
    finally:
        if zip_path is not None:
            cleanup(zip_path, args.keep)
