#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller --clean --noconfirm "macOS运维工具箱.spec"

echo "构建完成: dist/macOS运维工具箱.app"
echo "正式分发前请在 macOS 上完成 codesign 和 notarization。"

