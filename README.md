# nero-cli

> [!NOTE]
> This project is not affiliated with InvokeAI or any of its affiliates. It is a simple tool that streamlines the process of downloading and running the official InvokeAI installer on your local machine.

> [!WARNING]
> It has been mentioned in the discord channel that the InvokeAI team is working on an official new installer, no ETA. Once that is released, and if it has update capabilities, this tool will be deprecated and sunsetted.


## Overview

**nero-cli** is a simple CLI tool that streamlines the process of downloading Official InvokeAI release from github and running it on your local machine.
It is designed to be a simple allow you to quickly and easily pull the latest version, specify version, or rollback if you need to.


![screenshot](https://raw.githubusercontent.com/regiellis/nero-cli/refs/heads/main/screen.png)

## Why

I have serveral machines local and remote that I have InvokeAI installed on. I wanted a simple way to update/downgrade them without having to manually
download the release from github and install it on each machine. This tool allows me to do that. It also made sense to use the offical InvokeAI installer
instead roll a patch work that may not work as expected.


## Installation (Recommended)

You have a couple of options for installing/running the tool:

### Install [pipx](https://pipxproject.github.io/pipx/installation/), then run the tool with the following command

```bash
pipx install nero-cli
```

### Alternatively, you can install using `pip`

```bash
pip install .
```

## Usage // Available Commands

Once installed via pipx or pip:

```
usage: nero [-h] [--dry-run] [--download-only] [--latest] [--version VERSION] [--rollback] [--keep] [--download-dir DOWNLOAD_DIR] [--check] [--update-config]

Invoke Installer Script

options:
  -h, --help            show this help message and exit
  --dry-run             Perform a dry run without making any changes
  --download-only       Only download the installer without running it
  --latest              Check for the latest version and prompt for update
  --version VERSION     Specify a version to download and install
  --rollback            Rollback to the previous version
  --keep                Keep the downloaded file after installation
  --download-dir DOWNLOAD_DIR
                        Specify the directory to save downloads
  --check               Display current configuration and check for updates
  --update-config       Only update the configuration file with the current or specified version
```

## Dependencies

This tool requires Python 3.11 or higher and has the following dependencies:

- none

### Contact

For any inquiries, feedback, or suggestions, please feel free to open an issue on this repository.

### License

This project is licensed under the [MIT License](LICENSE).

---
