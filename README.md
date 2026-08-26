# 运维工具箱

电脑出现断网、系统变慢、磁盘空间不足、软件更新失败、开机异常等问题时，很多人不知道该从哪里开始排查。

**运维工具箱**把常用的检查和修复操作放在一个简单的工作台里，并针对 Windows、macOS、Linux 提供各自适用的工具。你可以先让内置 AI 助手分析问题，再按建议逐项检查，不需要记住一长串命令。

## 适合做什么

- **网络问题**：刷新 DNS、重新获取 IP、检查网关和端口，排查“能连 Wi-Fi 但打不开网页”等问题。
- **系统修复**：Windows 的 SFC/DISM 和网络组件修复，macOS 系统卷检查，Linux 服务与启动分析。
- **清理空间**：清理临时文件、浏览器缓存、回收站和日志，查找占用空间较大的文件。
- **安全检查**：查看防火墙、FileVault、Gatekeeper、失败登录和异常服务状态。
- **性能与硬件**：查看 CPU、内存、磁盘、电池、温度和系统运行情况。
- **系统工具**：快速打开任务管理器、活动监视器、终端、文件管理器和系统设置。

当前包含 Windows 78 项、macOS 44 项、Linux 43 项工具。程序会自动识别系统，只显示适合当前平台的功能。

## AI 助手怎么用

打开右上角的 **AI 助手**，直接用日常语言描述问题，例如：

> Wi-Fi 能连接，但是网页打不开，应该怎么办？

助手会根据当前系统的工具目录给出排查顺序和对应工具。它只会推荐已有功能，不会假装已经替你执行命令。

- 默认使用**离线诊断**，不需要网络，也不会上传问题。
- 如果电脑安装了 Ollama，可以切换到本机模型。
- 也可以自行配置兼容的在线模型接口；只有主动配置后，问题内容才会发送到该接口。

## 三步开始使用

1. 下载与你的系统对应的版本，或直接打开网页版。
2. 先打开 AI 助手描述问题，也可以使用搜索框查找工具。
3. 阅读工具说明后运行。带有“有风险”“管理员”或“需重启”提示的操作，会在执行前再次确认。

## 在线网页版

无需下载，打开即可使用：[运维工具箱网页版](https://yukineyuuna.github.io/ops-toolbox/)

网页版可以浏览全部工具、搜索问题、使用离线 AI 推荐、切换 Windows/macOS/Linux 目录、收藏工具、调整字体和主题。由于浏览器不能直接修改本机系统，清理文件、重启服务、修改防火墙等操作需要使用桌面版。

## 下载桌面版

前往 [最新版本下载页](https://github.com/YukineYuuna/ops-toolbox/releases/latest)，选择对应文件：

- [Windows：OpsToolbox-windows.exe](https://github.com/YukineYuuna/ops-toolbox/releases/download/v3.1.0/OpsToolbox-windows.exe)
  下载后双击即可运行；需要管理员权限的操作会在执行时提示。
- [macOS：OpsToolbox-macos.app.zip](https://github.com/YukineYuuna/ops-toolbox/releases/download/v3.1.0/OpsToolbox-macos.app.zip)
  解压后打开 App。首次打开若被系统拦截，请在“系统设置 → 隐私与安全性”中允许。
- [Linux：OpsToolbox-linux.tar.gz](https://github.com/YukineYuuna/ops-toolbox/releases/download/v3.1.0/OpsToolbox-linux.tar.gz)
  解压后运行 `./Linux运维工具箱`。如果界面无法启动，请先安装 WebKitGTK：

  ```bash
  sudo apt install python3-gi gir1.2-webkit2-4.1
  ```

## 离线使用和隐私

- 核心工具、界面、收藏记录和离线 AI 推荐都在本机运行，断网仍可使用。
- 壁纸联网更新只是可选功能；网络不可用时会继续使用本地壁纸缓存。
- 桌面端执行系统操作前会检查权限，并对可能有影响的操作再次确认。重要操作前请先保存工作并做好备份。
- 使用在线 AI 时，请不要发送密码、API Key、个人隐私或不必要的系统日志。

## 从源码运行

如果你希望自己运行或参与改进，准备 Python 3.10 或更高版本：

```bash
python -m pip install -r requirements.txt
python 运维工具箱.py
```

macOS 可以双击 `运维工具箱_mac.command`，Linux 可以运行 `chmod +x 运维工具箱_linux.sh && ./运维工具箱_linux.sh`。

## 项目组成

```text
运维工具箱.py       启动程序
modules/             平台工具、AI 助手和壁纸缓存
web/                 桌面端与网页版界面
tests/               跨平台工具目录检查
```

项目会持续补充更实用的诊断和修复功能。欢迎通过 [Issues](https://github.com/YukineYuuna/ops-toolbox/issues) 反馈问题或提出建议。
