#!/bin/bash
set -e

# update apt
# fix permissions for cron files if any
apt-get install -y build-essential python3-dev rustc cargo

# fix permissions for cron files if any
apt-get install -y build-essential python3-dev
if [ -f /etc/cron.d/* ]; then
    chmod 0644 /etc/cron.d/*
fi

# Prepare SSH daemon
bash /ins/setup_ssh.sh "$@"
