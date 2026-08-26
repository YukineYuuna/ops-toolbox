#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""macOS 工具数据 - 与 data.py（Windows）同结构，工具 id 尽量保持一致以复用诊断向导"""
from modules import unix_tools as ut

CATEGORIES = [
    ('network', '网络修复', '🌐'),
    ('storage', '磁盘与备份', '💾'),
    ('security', '安全与隐私', '🛡'),
    ('services', '服务与启动项', '🔄'),
    ('cleanup', '清理工具', '🧹'),
    ('packages', '软件与更新', '📦'),
    ('optimize', '性能优化', '⚡'),
    ('info', '系统信息', '📊'),
    ('tools', '系统工具', '🧰'),
]

FUNCTIONS = [
    # 网络修复
    {"id": "flush_dns", "name": "清理 DNS 缓存", "desc": "dscacheutil + mDNSResponder，解决域名解析异常、网页打不开", "category": "network", "icon": "🌐", "func": ut.flush_dns, "danger": False, "admin": True, "reboot": False},
    {"id": "release_renew_ip", "name": "重新获取 IP", "desc": "重新走 DHCP 获取 IP，解决 IP 冲突、获取不到 IP", "category": "network", "icon": "🌐", "func": ut.release_renew_ip, "danger": False, "admin": True, "reboot": False},
    {"id": "reset_network_full", "name": "重启网络服务", "desc": "关闭再开启 WiFi 并清理 DNS，解决大部分网络异常（会短暂断网）", "category": "network", "icon": "🌐", "func": ut.reset_network_full, "danger": True, "admin": True, "reboot": False},
    {"id": "clear_arp", "name": "清除 ARP 缓存", "desc": "清除 ARP 缓存，解决局域网内设备互访异常", "category": "network", "icon": "🌐", "func": ut.clear_arp, "danger": False, "admin": True, "reboot": False},
    {"id": "get_network_info", "name": "网络配置信息", "desc": "查看网络接口、IP 地址和 DNS 配置", "category": "network", "icon": "🌐", "func": ut.get_network_info, "danger": False, "admin": False, "reboot": False},
    # 清理工具
    {"id": "clean_temp_files", "name": "清理用户缓存", "desc": "清理 ~/Library/Caches 用户缓存文件", "category": "cleanup", "icon": "🧹", "func": ut.clean_temp_files, "danger": False, "admin": False, "reboot": False},
    {"id": "clean_recycle_bin", "name": "清空回收站", "desc": "清空 ~/.Trash 回收站", "category": "cleanup", "icon": "🧹", "func": ut.clean_recycle_bin, "danger": False, "admin": False, "reboot": False},
    {"id": "clean_browser_cache", "name": "清理浏览器缓存", "desc": "清理 Chrome / Firefox 浏览器缓存", "category": "cleanup", "icon": "🧹", "func": ut.clean_browser_cache, "danger": False, "admin": False, "reboot": False},
    {"id": "clean_logs_mac", "name": "清理用户日志", "desc": "清理 ~/Library/Logs 下的日志文件", "category": "cleanup", "icon": "🧹", "func": ut.clean_logs_mac, "danger": False, "admin": False, "reboot": False},
    {"id": "scan_large_files", "name": "扫描大文件", "desc": "扫描用户目录下大于 500MB 的文件", "category": "cleanup", "icon": "🧹", "func": ut.scan_large_files, "danger": False, "admin": False, "reboot": False},
    {"id": "analyze_disk_usage", "name": "分析磁盘占用", "desc": "查看磁盘使用率及用户目录各文件夹占用排行", "category": "cleanup", "icon": "🧹", "func": ut.analyze_disk_usage, "danger": False, "admin": False, "reboot": False},
    {"id": "full_cleanup", "name": "一键全面清理", "desc": "用户缓存 + 回收站 + 浏览器缓存，一次全清", "category": "cleanup", "icon": "🧹", "func": ut.full_cleanup, "danger": True, "admin": False, "reboot": False},
    # 性能优化
    {"id": "check_cpu_info", "name": "查看 CPU 信息", "desc": "查看 CPU 型号、核心数与当前负载", "category": "optimize", "icon": "⚡", "func": ut.check_cpu_info, "danger": False, "admin": False, "reboot": False},
    {"id": "check_memory_info", "name": "查看内存信息", "desc": "查看内存容量、使用与内存压力", "category": "optimize", "icon": "⚡", "func": ut.check_memory_info, "danger": False, "admin": False, "reboot": False},
    {"id": "check_startup_items", "name": "查看启动项", "desc": "查看非 Apple 的开机启动服务", "category": "optimize", "icon": "⚡", "func": ut.check_startup_items, "danger": False, "admin": False, "reboot": False},
    {"id": "purge_memory_mac", "name": "释放非活跃内存", "desc": "执行 purge 命令释放缓存内存，缓解内存压力", "category": "optimize", "icon": "⚡", "func": ut.purge_memory_mac, "danger": False, "admin": True, "reboot": False},
    {"id": "disable_visual_effects", "name": "减少视觉特效", "desc": "开启减弱透明度/动态效果，老机器更流畅", "category": "optimize", "icon": "⚡", "func": ut.disable_visual_effects, "danger": False, "admin": False, "reboot": False},
    {"id": "enable_visual_effects", "name": "恢复视觉效果", "desc": "恢复系统默认的透明度与动态效果", "category": "optimize", "icon": "⚡", "func": ut.enable_visual_effects, "danger": False, "admin": False, "reboot": False},
    # 系统信息
    {"id": "get_system_full_info", "name": "完整系统信息", "desc": "系统版本、CPU、内存、磁盘一览", "category": "info", "icon": "📊", "func": ut.get_system_full_info, "danger": False, "admin": False, "reboot": False},
    {"id": "get_os_version", "name": "操作系统版本", "desc": "查看 macOS 版本与构建号", "category": "info", "icon": "📊", "func": ut.get_os_version, "danger": False, "admin": False, "reboot": False},
    {"id": "get_recent_errors", "name": "最近系统错误", "desc": "查看最近 1 小时的系统错误日志", "category": "info", "icon": "📊", "func": ut.get_recent_errors, "danger": False, "admin": False, "reboot": False},
    {"id": "get_installed_software", "name": "已安装软件", "desc": "查看 /Applications 应用与 Homebrew 包", "category": "info", "icon": "📊", "func": ut.get_installed_software, "danger": False, "admin": False, "reboot": False},
    {"id": "get_running_services", "name": "进程资源占用", "desc": "查看 CPU 占用最高的进程", "category": "info", "icon": "📊", "func": ut.get_running_services, "danger": False, "admin": False, "reboot": False},
    # 系统工具
    {"id": "open_task_manager", "name": "活动监视器", "desc": "打开 macOS 活动监视器，查看进程与资源占用", "category": "tools", "icon": "🧰", "func": ut.open_task_manager, "danger": False, "admin": False, "reboot": False},
    {"id": "open_terminal", "name": "打开终端", "desc": "打开 Terminal 终端", "category": "tools", "icon": "🧰", "func": ut.open_terminal, "danger": False, "admin": False, "reboot": False},
    {"id": "open_files", "name": "打开访达", "desc": "打开 Finder 用户目录", "category": "tools", "icon": "🧰", "func": ut.open_files, "danger": False, "admin": False, "reboot": False},
    {"id": "open_settings", "name": "系统设置", "desc": "打开 macOS 系统设置", "category": "tools", "icon": "🧰", "func": ut.open_settings, "danger": False, "admin": False, "reboot": False},
    {"id": "open_network_connections", "name": "网络设置", "desc": "打开系统网络偏好设置", "category": "tools", "icon": "🧰", "func": ut.open_network_connections, "danger": False, "admin": False, "reboot": False},

    # macOS 专属网络诊断
    {"id": "check_gateway_connectivity", "name": "网关与公网连通测试", "desc": "检测默认网关与公共网络连通性，区分局域网和外网故障", "category": "network", "icon": "🌐", "func": ut.check_gateway_connectivity, "danger": False, "admin": False, "reboot": False},
    {"id": "check_dns_resolution", "name": "DNS 解析诊断", "desc": "检查 dscacheutil 解析结果与 scutil DNS 配置", "category": "network", "icon": "🌐", "func": ut.check_dns_resolution, "danger": False, "admin": False, "reboot": False},
    {"id": "list_listening_ports", "name": "查看监听端口", "desc": "使用 lsof 查看本机 TCP 监听端口和对应进程", "category": "network", "icon": "🌐", "func": ut.list_listening_ports, "danger": False, "admin": False, "reboot": False},

    # APFS、磁盘与备份
    {"id": "check_disk_layout", "name": "APFS 磁盘布局", "desc": "查看 APFS 容器、系统卷、容量与 SMART 状态", "category": "storage", "icon": "💾", "func": ut.check_disk_layout, "danger": False, "admin": False, "reboot": False},
    {"id": "verify_system_volume_mac", "name": "验证系统卷", "desc": "使用 diskutil 对启动卷进行只读完整性验证", "category": "storage", "icon": "💾", "func": ut.verify_system_volume_mac, "danger": False, "admin": False, "reboot": False},
    {"id": "check_apfs_snapshots_mac", "name": "查看本地快照", "desc": "列出 Time Machine 在 APFS 系统卷上的本地快照", "category": "storage", "icon": "💾", "func": ut.check_apfs_snapshots_mac, "danger": False, "admin": False, "reboot": False},
    {"id": "check_time_machine_mac", "name": "Time Machine 状态", "desc": "查看当前备份状态和最近一次可用备份", "category": "storage", "icon": "💾", "func": ut.check_time_machine_mac, "danger": False, "admin": False, "reboot": False},

    # macOS 安全状态
    {"id": "check_filevault_mac", "name": "FileVault 状态", "desc": "检查启动磁盘是否启用 FileVault 加密", "category": "security", "icon": "🛡", "func": ut.check_filevault_mac, "danger": False, "admin": False, "reboot": False},
    {"id": "check_gatekeeper_mac", "name": "Gatekeeper 与 SIP", "desc": "检查应用来源验证和系统完整性保护状态", "category": "security", "icon": "🛡", "func": ut.check_gatekeeper_mac, "danger": False, "admin": False, "reboot": False},
    {"id": "check_firewall_mac", "name": "应用防火墙状态", "desc": "查看 macOS 应用防火墙与隐身模式状态", "category": "security", "icon": "🛡", "func": ut.check_firewall_mac, "danger": False, "admin": False, "reboot": False},

    # launchd 与系统服务
    {"id": "check_launch_agents_mac", "name": "LaunchAgents 检查", "desc": "列出用户与系统级 LaunchAgents / LaunchDaemons", "category": "services", "icon": "🔄", "func": ut.check_launch_agents_mac, "danger": False, "admin": False, "reboot": False},
    {"id": "restart_audio_mac", "name": "重启 Core Audio", "desc": "重启 coreaudiod，修复无声、音频设备卡住等问题", "category": "services", "icon": "🔄", "func": ut.restart_audio_mac, "danger": True, "admin": True, "reboot": False},

    # 软件与更新
    {"id": "check_software_updates_mac", "name": "检查 macOS 更新", "desc": "使用 softwareupdate 列出当前可用的系统更新", "category": "packages", "icon": "📦", "func": ut.check_software_updates_mac, "danger": False, "admin": False, "reboot": False},
    {"id": "brew_doctor_mac", "name": "Homebrew 健康检查", "desc": "运行 brew doctor 并列出可更新的软件包", "category": "packages", "icon": "📦", "func": ut.brew_doctor_mac, "danger": False, "admin": False, "reboot": False},

    # Apple 硬件状态
    {"id": "check_battery_health", "name": "电池健康", "desc": "查看循环次数、健康状况和最大容量", "category": "optimize", "icon": "⚡", "func": ut.check_battery_health, "danger": False, "admin": False, "reboot": False},
    {"id": "check_thermal_state", "name": "温控与电源状态", "desc": "查看系统温控警告和当前电池/电源状态", "category": "optimize", "icon": "⚡", "func": ut.check_thermal_state, "danger": False, "admin": False, "reboot": False},
]
