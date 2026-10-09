#!/bin/bash
# Preserve suites and signing keys; replace only the runner's Azure mirror URL.
set -euo pipefail
for apt_source in /etc/apt/apt-mirrors.txt /etc/apt/sources.list /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources; do
  if [ -f "$apt_source" ]; then
    sudo sed -i 's|http://azure.archive.ubuntu.com/ubuntu|https://archive.ubuntu.com/ubuntu|g' "$apt_source"
  fi
done
