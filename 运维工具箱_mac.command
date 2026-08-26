#!/bin/bash
# macOS 运维工具箱 启动器
# 使用方法：先在本文件上右键 →「打开」允许运行；之后双击即可
# 如提示无权限，终端执行一次：chmod +x 运维工具箱_mac.command

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[错误] 未找到 python3"
    echo "请先安装 python.org 官方 Python 3.10+，或执行: brew install python@3"
    read -r -p "按回车退出..."
    exit 1
fi

if ! python3 -c "import webview" 2>/dev/null; then
    echo "[提示] 未安装 pywebview，将尝试 Tkinter 兼容界面。"
    echo "完整界面可安装: pip3 install -r requirements.txt"
    if ! python3 -c "import tkinter" 2>/dev/null; then
        echo "[错误] WebView 与 Tkinter 均不可用"
        echo "如使用 Homebrew Python 请执行: brew install python-tk"
        read -r -p "按回车退出..."
        exit 1
    fi
fi

echo "正在启动 macOS 运维工具箱..."
python3 运维工具箱.py
