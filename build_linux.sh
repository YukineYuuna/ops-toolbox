#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller --clean --noconfirm "Linux运维工具箱.spec"

echo "构建完成: dist/Linux运维工具箱"
