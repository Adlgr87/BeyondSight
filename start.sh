#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "BeyondSight - Quick start for Unix/macOS"
echo "=========================================="

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 is not installed."
  echo "Install Python 3.10+ and run this script again."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "[INFO] Creating virtual environment at .venv ..."
  python3 -m venv .venv
fi

echo "[INFO] Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[INFO] Upgrading pip..."
python -m pip install --upgrade pip

echo "[INFO] Installing dependencies..."
pip install -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  echo "[INFO] Creating .env from .env.example ..."
  cp .env.example .env
  echo "[INFO] .env created. Edit it to add API keys if needed."
fi

echo "[INFO] Launching BeyondSight at http://localhost:8501 ..."
exec streamlit run app.py
