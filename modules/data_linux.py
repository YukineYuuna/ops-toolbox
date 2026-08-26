#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Linux 工具数据 - 与 data.py（Windows）同结构，工具 id 尽量保持一致以复用诊断向导"""
from modules import unix_tools as ut

CATEGORIES = [
    ('network', '网络修复', '🌐'),
    ('storage', '磁盘与文件系统', '💾'),
    ('security', '安全与防火墙', '🛡'),
    ('services', 'systemd 服务', '🔄'),
    ('boot', '启动诊断', '🔧'),
    ('cleanup', '清理工具', '🧹'),
    ('packages', '软件包维护', '📦'),
    ('optimize', '性能优化', '⚡'),
    ('info', '系统信息', '📊'),
    ('tools', '系统工具', '🧰'),
]

FUNCTIONS = [
    # 网络修复
    {"id": "flush_dns", "name": "清理 DNS 缓存", "desc": "清理 systemd-resolved/nscd/dnsmasq 的 DNS 缓存", "category": "network", "icon": "🌐", "func": ut.flush_dns, "danger": False, "admin": True, "reboot": False},
    {"id": "release_renew_ip", "name": "重新获取 IP", "desc": "通过 NetworkManager/dhclient 重新获取 IP，解决 IP 冲突", "category": "network", "icon": "🌐", "func": ut.release_renew_ip, "danger": False, "admin": True, "reboot": False},
    {"id": "reset_network_full", "name": "重启网络服务", "desc": "重启 NetworkManager 网络服务，解决大部分网络异常（会短暂断网）", "category": "network", "icon": "🌐", "func": ut.reset_network_full, "danger": True, "admin": True, "reboot": False},
    {"id": "clear_arp", "name": "清除 ARP 缓存", "desc": "清除 ARP 邻居表，解决局域网内设备互访异常", "category": "network", "icon": "🌐", "func": ut.clear_arp, "danger": False, "admin": True, "reboot": False},
    {"id": "get_network_info", "name": "网络配置信息", "desc": "查看网络接口、路由表和 DNS 配置", "category": "network", "icon": "🌐", "func": ut.get_network_info, "danger": False, "admin": False, "reboot": False},
    # 清理工具
    {"id": "clean_temp_files", "name": "清理用户缓存", "desc": "清理 ~/.cache 用户缓存文件", "category": "cleanup", "icon": "🧹", "func": ut.clean_temp_files, "danger": False, "admin": False, "reboot": False},
    {"id": "clean_recycle_bin", "name": "清空回收站", "desc": "清空 ~/.local/share/Trash 回收站", "category": "cleanup", "icon": "🧹", "func": ut.clean_recycle_bin, "danger": False, "admin": False, "reboot": False},
    {"id": "clean_browser_cache", "name": "清理浏览器缓存", "desc": "清理 Chrome / Chromium / Firefox 浏览器缓存", "category": "cleanup", "icon": "🧹", "func": ut.clean_browser_cache, "danger": False, "admin": False, "reboot": False},
    {"id": "clean_journal_linux", "name": "清理系统日志", "desc": "journalctl 日志只保留最近 7 天，可释放大量空间", "category": "cleanup", "icon": "🧹", "func": ut.clean_journal_linux, "danger": False, "admin": True, "reboot": False},
    {"id": "clean_apt_cache", "name": "清理 apt 缓存", "desc": "apt-get clean + autoremove，清理包缓存和无用依赖（Debian/Ubuntu）", "category": "cleanup", "icon": "🧹", "func": ut.clean_apt_cache, "danger": False, "admin": True, "reboot": False},
    {"id": "scan_large_files", "name": "扫描大文件", "desc": "扫描用户目录下大于 500MB 的文件", "category": "cleanup", "icon": "🧹", "func": ut.scan_large_files, "danger": False, "admin": False, "reboot": False},
    {"id": "analyze_disk_usage", "name": "分析磁盘占用", "desc": "查看磁盘使用率及用户目录各文件夹占用排行", "category": "cleanup", "icon": "🧹", "func": ut.analyze_disk_usage, "danger": False, "admin": False, "reboot": False},
    {"id": "full_cleanup", "name": "一键全面清理", "desc": "用户缓存 + 回收站 + 浏览器缓存，一次全清", "category": "cleanup", "icon": "🧹", "func": ut.full_cleanup, "danger": True, "admin": False, "reboot": False},
    # 性能优化
    {"id": "check_cpu_info", "name": "查看 CPU 信息", "desc": "查看 CPU 型号、核心数与当前负载", "category": "optimize", "icon": "⚡", "func": ut.check_cpu_info, "danger": False, "admin": False, "reboot": False},
    {"id": "check_memory_info", "name": "查看内存信息", "desc": "查看内存容量与使用情况", "category": "optimize", "icon": "⚡", "func": ut.check_memory_info, "danger": False, "admin": False, "reboot": False},
    {"id": "check_startup_items", "name": "查看启动项", "desc": "查看开机自启的 systemd 服务", "category": "optimize", "icon": "⚡", "func": ut.check_startup_items, "danger": False, "admin": False, "reboot": False},
    {"id": "drop_caches_linux", "name": "释放页缓存", "desc": "sync 后释放 page cache，回收内存（不影响运行中的程序）", "category": "optimize", "icon": "⚡", "func": ut.drop_caches_linux, "danger": False, "admin": True, "reboot": False},
    {"id": "disable_visual_effects", "name": "关闭桌面动画", "desc": "关闭 GNOME 桌面动画特效，老机器更流畅", "category": "optimize", "icon": "⚡", "func": ut.disable_visual_effects, "danger": False, "admin": False, "reboot": False},
    {"id": "enable_visual_effects", "name": "恢复桌面动画", "desc": "恢复 GNOME 桌面默认动画效果", "category": "optimize", "icon": "⚡", "func": ut.enable_visual_effects, "danger": False, "admin": False, "reboot": False},
    # 系统信息
    {"id": "get_system_full_info", "name": "完整系统信息", "desc": "发行版、内核、CPU、内存、磁盘一览", "category": "info", "icon": "📊", "func": ut.get_system_full_info, "danger": False, "admin": False, "reboot": False},
    {"id": "get_os_version", "name": "操作系统版本", "desc": "查看发行版与内核版本", "category": "info", "icon": "📊", "func": ut.get_os_version, "danger": False, "admin": False, "reboot": False},
    {"id": "get_recent_errors", "name": "最近系统错误", "desc": "查看 journalctl 中最近的错误日志", "category": "info", "icon": "📊", "func": ut.get_recent_errors, "danger": False, "admin": False, "reboot": False},
    {"id": "get_installed_software", "name": "已安装软件", "desc": "查看 dpkg/rpm/flatpak 安装的软件包", "category": "info", "icon": "📊", "func": ut.get_installed_software, "danger": False, "admin": False, "reboot": False},
    {"id": "get_running_services", "name": "运行中的服务", "desc": "查看正在运行的 systemd 服务", "category": "info", "icon": "📊", "func": ut.get_running_services, "danger": False, "admin": False, "reboot": False},
    # 系统工具
    {"id": "open_task_manager", "name": "系统监视器", "desc": "打开 GNOME/MATE 系统监视器，查看进程与资源占用", "category": "tools", "icon": "🧰", "func": ut.open_task_manager, "danger": False, "admin": False, "reboot": False},
    {"id": "open_terminal", "name": "打开终端", "desc": "打开系统终端模拟器", "category": "tools", "icon": "🧰", "func": ut.open_terminal, "danger": False, "admin": False, "reboot": False},
    {"id": "open_files", "name": "文件管理器", "desc": "打开文件管理器用户目录", "category": "tools", "icon": "🧰", "func": ut.open_files, "danger": False, "admin": False, "reboot": False},
    {"id": "open_settings", "name": "系统设置", "desc": "打开桌面环境系统设置", "category": "tools", "icon": "🧰", "func": ut.open_settings, "danger": False, "admin": False, "reboot": False},
    {"id": "open_network_connections", "name": "网络设置", "desc": "打开网络连接编辑器", "category": "tools", "icon": "🧰", "func": ut.open_network_connections, "danger": False, "admin": False, "reboot": False},

    # Linux 专属网络诊断
    {"id": "check_gateway_connectivity", "name": "网关与公网连通测试", "desc": "通过 ip route 和 ping 区分网关、外网连接故障", "category": "network", "icon": "🌐", "func": ut.check_gateway_connectivity, "danger": False, "admin": False, "reboot": False},
    {"id": "check_dns_resolution", "name": "DNS 解析诊断", "desc": "检查 getent 解析结果与 resolvectl / resolv.conf 配置", "category": "network", "icon": "🌐", "func": ut.check_dns_resolution, "danger": False, "admin": False, "reboot": False},
    {"id": "list_listening_ports", "name": "查看监听端口", "desc": "使用 ss 或 netstat 查看监听端口和对应进程", "category": "network", "icon": "🌐", "func": ut.list_listening_ports, "danger": False, "admin": False, "reboot": False},

    # 磁盘与文件系统
    {"id": "check_disk_layout", "name": "磁盘与挂载点", "desc": "使用 lsblk 和 findmnt 查看文件系统、容量、挂载点与磁盘型号", "category": "storage", "icon": "💾", "func": ut.check_disk_layout, "danger": False, "admin": False, "reboot": False},
    {"id": "check_smart_linux", "name": "SMART 健康摘要", "desc": "读取 smartctl 检测到的物理磁盘健康结果", "category": "storage", "icon": "💾", "func": ut.check_smart_linux, "danger": False, "admin": False, "reboot": False},

    # 安全与访问
    {"id": "check_firewall_linux", "name": "防火墙状态", "desc": "自动识别 ufw、firewalld 或 nftables 并显示当前规则", "category": "security", "icon": "🛡", "func": ut.check_firewall_linux, "danger": False, "admin": False, "reboot": False},
    {"id": "check_failed_logins_linux", "name": "失败登录记录", "desc": "查看最近失败的本地或 SSH 登录尝试", "category": "security", "icon": "🛡", "func": ut.check_failed_logins_linux, "danger": False, "admin": True, "reboot": False},

    # systemd 服务与启动
    {"id": "check_failed_services_linux", "name": "失败的 systemd 服务", "desc": "列出系统和用户会话中启动失败的 systemd 单元", "category": "services", "icon": "🔄", "func": ut.check_failed_services_linux, "danger": False, "admin": False, "reboot": False},
    {"id": "restart_audio_linux", "name": "重启桌面音频服务", "desc": "重启 PipeWire / PulseAudio 用户服务，修复桌面无声", "category": "services", "icon": "🔄", "func": ut.restart_audio_linux, "danger": True, "admin": False, "reboot": False},
    {"id": "analyze_boot_linux", "name": "systemd 启动分析", "desc": "查看本次启动耗时、慢单元和错误日志", "category": "boot", "icon": "🔧", "func": ut.analyze_boot_linux, "danger": False, "admin": False, "reboot": False},

    # 发行版软件包
    {"id": "check_package_updates_linux", "name": "检查软件包更新", "desc": "自动识别 apt、dnf、pacman 或 zypper 并列出更新", "category": "packages", "icon": "📦", "func": ut.check_package_updates_linux, "danger": False, "admin": False, "reboot": False},
    {"id": "repair_packages_linux", "name": "修复软件包状态", "desc": "按发行版修复未配置或依赖损坏的软件包", "category": "packages", "icon": "📦", "func": ut.repair_packages_linux, "danger": True, "admin": True, "reboot": False},

    # 硬件状态
    {"id": "check_battery_health", "name": "电池健康", "desc": "通过 UPower 或 ACPI 查看容量、状态与剩余时间", "category": "optimize", "icon": "⚡", "func": ut.check_battery_health, "danger": False, "admin": False, "reboot": False},
    {"id": "check_thermal_state", "name": "温度传感器", "desc": "读取 lm-sensors 或 thermal_zone 的温度数据", "category": "optimize", "icon": "⚡", "func": ut.check_thermal_state, "danger": False, "admin": False, "reboot": False},
]
