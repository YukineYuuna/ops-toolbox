#!/bin/bash
# Linux 运维工具箱 启动器
# 使用方法：chmod +x 运维工具箱_linux.sh && ./运维工具箱_linux.sh
# 或右键 → 作为程序运行

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[错误] 未找到 python3"
    echo "Debian/Ubuntu: sudo apt install python3"
    echo "Fedora:        sudo dnf install python3"
    read -r -p "按回车退出..."
    exit 1
fi

if ! python3 -c "import webview, gi" 2>/dev/null; then
    echo "[提示] WebView 依赖不完整，将尝试 Tkinter 兼容界面。"
    echo "完整界面可安装: pip3 install -r requirements.txt"
    echo "Debian/Ubuntu 还需: sudo apt install python3-gi gir1.2-webkit2-4.1"
    if ! python3 -c "import tkinter" 2>/dev/null; then
        echo "[错误] WebView 与 Tkinter 均不可用"
        echo "Debian/Ubuntu: sudo apt install python3-tk"
        echo "Fedora:        sudo dnf install python3-tkinter"
        echo "Arch:          sudo pacman -S tk"
        read -r -p "按回车退出..."
        exit 1
    fi
fi

echo "正在启动 Linux 运维工具箱..."
python3 运维工具箱.py
