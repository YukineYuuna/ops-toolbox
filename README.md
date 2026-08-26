# 运维工具箱

一个离线优先、跨平台的桌面运维工作台。它使用本地 Python 工具执行系统诊断与维护，并提供响应式毛玻璃界面、明暗主题、可调字号、壁纸轮播、收藏/最近使用和 AI 故障分流。

项目为 Windows、macOS、Linux 分别维护工具目录。平台不同，显示的操作也不同：Windows 使用 PowerShell、DISM、SFC、Winsock、注册表和系统管理工具；macOS 使用 `dscacheutil`、`diskutil`、`launchctl`、FileVault、Gatekeeper、Time Machine 等；Linux 自动适配 `systemd`、NetworkManager、`ufw/firewalld/nftables`、`apt/dnf/pacman/zypper`、SMART 和桌面环境工具。

## 功能概览

| 模块 | 说明 |
| --- | --- |
| 网络修复 | DNS、DHCP/IP、ARP、网关、公网连通、监听端口和网络服务诊断 |
| 系统与启动 | Windows SFC/DISM/BCD，Linux systemd 启动分析，macOS 系统卷验证 |
| 清理与存储 | 临时文件、浏览器缓存、回收站、日志、大文件、磁盘布局和 SMART |
| 安全与服务 | 防火墙、FileVault、Gatekeeper/SIP、失败登录、失败服务和启动项 |
| 性能与信息 | CPU、内存、电池、温度、磁盘、系统版本、已安装软件和运行服务 |
| 本地 AI 助手 | 默认离线关键词分流；可选本机 Ollama；可选 OpenAI 兼容 HTTPS 接口 |
| 壁纸 | 内置离线 WebP 兜底；桌面端可多次触发 API 请求并缓存去重后的新图 |

当前目录规模：Windows 78 项、macOS 44 项、Linux 43 项。每个平台只显示适合该系统的命令和管理入口。

## 直接使用网页版

打开仓库的 GitHub Pages 地址即可使用，无需下载或安装。网页版会自动识别浏览器平台，也可以在页面顶部切换 Windows、macOS、Linux 工具目录。浏览器安全沙箱不允许网页直接执行本机命令，因此网页版提供完整的目录浏览、搜索、收藏、主题、字号、壁纸和离线 AI 推荐；需要清理磁盘、重启服务、修改防火墙等操作时，请下载桌面端。

发布后地址为：`https://<你的 GitHub 用户名>.github.io/<仓库名>/`。`pages.yml` 会在 `main` 分支更新后自动部署。

## 下载桌面端

进入 [Releases](../../releases/latest) 下载对应文件：

- **Windows**：`OpsToolbox-windows.exe`，下载后双击运行。需要管理员权限的工具会在执行前提示。
- **macOS**：`OpsToolbox-macos.app.zip`，解压后打开 App。首次运行若出现 Gatekeeper 提示，请在“系统设置 → 隐私与安全性”中允许；正式分发时建议由发布者签名和公证。
- **Linux**：`OpsToolbox-linux.tar.gz`，解压后运行 `./Linux运维工具箱`。桌面 WebView 需要 WebKitGTK；Debian/Ubuntu 可执行：

  ```bash
  sudo apt install python3-gi gir1.2-webkit2-4.1
  ```

Release 由 GitHub Actions 在真实的 `windows-latest`、`macos-latest` 和 `ubuntu-22.04` 运行器上构建。每个平台还会运行 Python 编译检查和工具目录契约测试。

## 从源码运行

需要 Python 3.10+：

```bash
python -m pip install -r requirements.txt
python 运维工具箱.py
```

macOS 可双击 `运维工具箱_mac.command`，Linux 可执行 `chmod +x 运维工具箱_linux.sh && ./运维工具箱_linux.sh`。如果没有 pywebview，程序会尝试使用 Tkinter 兼容界面。

## 离线与联网边界

- 核心工具、界面资源、收藏、最近使用和离线 AI 推荐均在本机运行，不依赖网络。
- 壁纸 API 仅用于联网增强；下载失败、断网或接口重复返回时，继续使用本地缓存。
- AI 默认是“离线推荐”，不会上传用户问题。Ollama 请求发往本机 `127.0.0.1`；在线兼容接口只有在用户主动配置 API Key 后才会发送问题，并强制要求 HTTPS。
- API Key 默认只保存在当前会话；勾选“记住 Key”后写入用户配置目录的权限受限文件。不要把该文件提交到 Git。

## 配置与安全

配置目录：

- Windows：`%APPDATA%\\OpsToolbox`
- macOS：`~/Library/Application Support/OpsToolbox`
- Linux：`$XDG_CONFIG_HOME/ops-toolbox` 或 `~/.config/ops-toolbox`

壁纸接口地址通过环境变量 `TOOLBOX_WALLPAPER_API_URL` 配置。项目不会在公开代码中内置访问令牌；如使用需要令牌的接口，请在本机环境变量中设置完整 URL。壁纸提供方控制图片版权，公开再分发前请确认图片和 API 的使用条款。

带“有风险”“管理员”或“需重启”标签的操作可能修改系统状态。工具详情页会再次确认，仍建议先运行只读检查并确保有备份。

## 构建

本地构建命令：

```bash
# Windows
python -m PyInstaller --clean --noconfirm Windows运维工具箱_v3.spec

# macOS
python -m PyInstaller --clean --noconfirm macOS运维工具箱.spec

# Linux
python -m PyInstaller --clean --noconfirm Linux运维工具箱.spec
```

提交到 `main` 或推送 `v*.*.*` 标签会触发 `.github/workflows/build.yml`。推送版本标签后，三个构建任务会把安装包附加到同一个 GitHub Release。

## 项目结构

```text
运维工具箱.py          启动器
modules/                平台检测、工具实现、WebView 桥接和壁纸缓存
web/                    毛玻璃界面、Lucide 图标和离线壁纸
tests/                  跨平台工具目录契约测试
.github/workflows/      三端构建与 GitHub Pages 部署
```

本项目暂未指定开源许可证。若要以特定许可证发布，请在仓库设置中明确添加与项目依赖兼容的许可证文件。
