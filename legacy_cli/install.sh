#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[*] Checking Python 3..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] Python 3 not found. Attempting automatic install..."
  if [[ "$OSTYPE" == "darwin"* ]]; then
    command -v brew >/dev/null 2>&1 || { echo "[!] Homebrew not found. Install it first."; exit 1; }
    brew install python@3
    export PATH="/opt/homebrew/opt/python@3/bin:$PATH"
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip
  else
    echo "[!] Unsupported OS. Please install Python 3 manually."
    exit 1
  fi
fi

echo "[*] Upgrading pip..."
python3 -m pip install --upgrade pip

echo "[*] Installing Python packages..."
python3 -m pip install -r requirements.txt

echo "[*] Installing Playwright browser..."
python3 -m playwright install chromium

echo "[*] Running script..."
python3 check_hddt_cl_v8.py
