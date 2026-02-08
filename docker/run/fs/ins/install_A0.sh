#!/bin/bash
set -e

# Exit immediately if a command exits with a non-zero status.
# set -e

# branch from parameter
if [ -z "$1" ]; then
    echo "Error: Branch parameter is empty. Please provide a valid branch name."
    exit 1
fi
BRANCH="$1"

if [ "$BRANCH" = "local" ]; then
    # For local branch, use the files
    echo "Using local dev files in /git/agent-zero"
    # List all files recursively in the target directory
    # echo "All files in /git/agent-zero (recursive):"
    # find "/git/agent-zero" -type f | sort
else
    # For other branches, clone from GitHub
    echo "Cloning repository from branch $BRANCH..."
    git clone -b "$BRANCH" "https://github.com/agent0ai/agent-zero" "/git/agent-zero" || {
        echo "CRITICAL ERROR: Failed to clone repository. Branch: $BRANCH"
        exit 1
    }
fi

. "/ins/setup_venv.sh" "$@"

# moved to base image
# # Ensure the virtual environment and pip setup
# pip install --upgrade pip ipython requests
# # Install some packages in specific variants
# pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining A0 python packages
# Deep Fix: Handle openai-whisper build issues on Kali/Python 3.12
echo "Installing build dependencies..."
pip install --upgrade pip "setuptools<70" wheel setuptools-rust

echo "Installing critical dependencies..."
pip install tiktoken --verbose
# Use --no-build-isolation to use the system packages (rust, etc) we just installed
pip install openai-whisper==20240930 --no-build-isolation --verbose

echo "Installing remaining requirements via uv..."
uv pip install -r /git/agent-zero/requirements.txt
# override for packages that have unnecessarily strict dependencies
uv pip install -r /git/agent-zero/requirements2.txt

# install playwright
bash /ins/install_playwright.sh "$@"

# Preload A0
python /git/agent-zero/preload.py --dockerized=true
