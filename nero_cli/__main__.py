import sys
import argparse

from .cli import nero


def main() -> None:
    parser = argparse.ArgumentParser(description="Invoke Installer Script")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making any changes",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download the installer without running it",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Check for the latest version and prompt for update",
    )
    parser.add_argument("--version", help="Specify a version to download and install")
    parser.add_argument(
        "--rollback", action="store_true", help="Rollback to the previous version"
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the downloaded file after installation",
    )
    parser.add_argument(
        "--list-versions",
        action="store_true",
        help="List available versions of InvokeAI",
    )
    # parser.add_argument(
    #     "--use-pyenv",
    #     action="store_true",
    #     help="Use pyenv to set Python version even if system Python is inadequate",
    # )
    parser.add_argument(
        "--download-dir", help="Specify the directory to save downloads"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Display current configuration and check for updates",
    )
    parser.add_argument(
        "--update-config",
        action="store_true",
        help="Only update the configuration file with the current or specified version",
    )
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
    else:
        nero(args)
