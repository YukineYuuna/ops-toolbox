#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""macOS / Linux 运维工具实现 - 与 Windows 各模块函数签名一致（log=None 返回 bool）
需要 root 的操作：macOS 弹系统授权框（osascript），Linux 用 pkexec/sudo。"""
import os

from modules import utils
from modules.platform_detect import IS_MAC, IS_LINUX

HOME = os.path.expanduser('~')


def _run(cmd, log=None):
    return utils.run_cmd(cmd, log)[0]


def _run_admin(cmd, log=None):
    """以管理员/root 身份执行命令"""
    if utils.is_admin():
        return _run(cmd, log)
    if IS_MAC:
        escaped = cmd.replace('\\', '\\\\').replace('"', '\\"')
        return _run('osascript -e \'do shell script "{}" with administrator privileges\''.format(escaped), log)
    if IS_LINUX:
        ok, _ = utils.run_cmd('which pkexec', None)
        quoted = cmd.replace("'", "'\\''")
        if ok:
            return _run("pkexec sh -c '{}'".format(quoted), log)
        return _run("sudo sh -c '{}'".format(quoted), log)
    return False


# ==================== 网络 ====================

def flush_dns(log=None):
    """清理 DNS 缓存"""
    if log:
        log('正在清理 DNS 缓存...')
    if IS_MAC:
        return _run_admin('dscacheutil -flushcache && killall -HUP mDNSResponder', log)
    cmd = ('(resolvectl flush-caches 2>/dev/null || systemd-resolve --flush-caches 2>/dev/null '
           '|| nscd -i hosts 2>/dev/null || service dnsmasq restart 2>/dev/null || echo 无系统DNS缓存服务)')
    return _run_admin(cmd, log)


def release_renew_ip(log=None):
    """释放并重新获取 IP（DHCP）"""
    if log:
        log('正在重新获取 IP 地址，网络会短暂中断...')
    if IS_MAC:
        return _run_admin('ipconfig set en0 BOOTP && sleep 1 && ipconfig set en0 DHCP', log)
    cmd = ('(nmcli networking off && sleep 1 && nmcli networking on) 2>/dev/null '
           '|| (dhclient -r && dhclient) 2>/dev/null')
    return _run_admin(cmd, log)


def reset_network_full(log=None):
    """重启网络服务（相当于 Windows 的网络重置）"""
    if log:
        log('正在重启网络服务...')
    if IS_MAC:
        return _run_admin('networksetup -setairportpower en0 off && sleep 2 && networksetup -setairportpower en0 on '
                          '&& dscacheutil -flushcache', log)
    cmd = ('(systemctl restart NetworkManager || service network-manager restart '
           '|| systemctl restart networking) 2>/dev/null')
    return _run_admin(cmd, log)


def clear_arp(log=None):
    """清除 ARP 缓存"""
    if IS_MAC:
        return _run_admin('arp -a -d', log)
    return _run_admin('ip neigh flush all', log)


def get_network_info(log=None):
    """查看网络配置信息"""
    if IS_MAC:
        return _run('echo "== 网络接口 ==" && ifconfig | grep -E "^[a-z]|inet " && '
                    'echo "== DNS ==" && scutil --dns | grep nameserver | head -5', log)
    return _run('echo "== 网络接口 ==" && ip -brief addr && echo "== 路由 ==" && ip route && '
                'echo "== DNS ==" && cat /etc/resolv.conf | grep nameserver', log)


# ==================== 清理 ====================

def clean_temp_files(log=None):
    """清理用户缓存目录（mac: ~/Library/Caches，linux: ~/.cache）"""
    if IS_MAC:
        return _run('rm -rf ~/Library/Caches/* 2>/dev/null; echo 用户缓存已清理', log)
    return _run('rm -rf ~/.cache/* 2>/dev/null; echo 用户缓存已清理', log)


def clean_recycle_bin(log=None):
    """清空回收站"""
    if IS_MAC:
        return _run('rm -rf ~/.Trash/* 2>/dev/null; echo 回收站已清空', log)
    return _run('rm -rf ~/.local/share/Trash/files/* ~/.local/share/Trash/info/* 2>/dev/null; echo 回收站已清空', log)


def clean_browser_cache(log=None):
    """清理 Chrome / Firefox 浏览器缓存"""
    if IS_MAC:
        return _run('rm -rf "$HOME/Library/Caches/Google/Chrome" "$HOME/Library/Caches/Mozilla" '
                    '"$HOME/Library/Application Support/Google/Chrome/Default/Service Worker/CacheStorage" 2>/dev/null; '
                    'echo 浏览器缓存已清理', log)
    return _run('rm -rf ~/.cache/google-chrome ~/.cache/chromium ~/.cache/mozilla 2>/dev/null; echo 浏览器缓存已清理', log)


def scan_large_files(log=None):
    """扫描用户目录下大于 500MB 的文件"""
    return _run('find ~ -type f -size +500M 2>/dev/null | head -30', log)


def analyze_disk_usage(log=None):
    """分析磁盘占用：整体使用 + 用户目录各文件夹排行"""
    return _run('echo "== 磁盘使用 ==" && df -h / ~ 2>/dev/null | sort -u && '
                'echo "== 目录占用 TOP15 ==" && du -sh ~/* ~/.[!.]* 2>/dev/null | sort -rh | head -15', log)


def full_cleanup(log=None):
    """一键清理：用户缓存 + 回收站 + 浏览器缓存"""
    ok = True
    ok = clean_temp_files(log) and ok
    ok = clean_recycle_bin(log) and ok
    ok = clean_browser_cache(log) and ok
    return ok


def clean_logs_mac(log=None):
    """清理用户日志（macOS）"""
    return _run('rm -rf ~/Library/Logs/* 2>/dev/null; echo 用户日志已清理', log)


def clean_journal_linux(log=None):
    """清理 systemd 日志（保留最近 7 天）"""
    return _run_admin('journalctl --vacuum-time=7d', log)


def clean_apt_cache(log=None):
    """清理 apt 包缓存并卸载无用依赖（Debian/Ubuntu）"""
    return _run_admin('apt-get clean && apt-get autoremove -y', log)


# ==================== 系统信息 ====================

def get_system_full_info(log=None):
    """完整系统信息"""
    if IS_MAC:
        return _run('sw_vers && uname -a && echo "== CPU ==" && sysctl -n machdep.cpu.brand_string && '
                    'echo "== 内存 ==" && echo "$(( $(sysctl -n hw.memsize) / 1073741824 )) GB" && '
                    'echo "== 磁盘 ==" && df -h /', log)
    return _run('(lsb_release -a 2>/dev/null; uname -a; echo "== CPU ==" && lscpu | head -12; '
                'echo "== 内存 ==" && free -h; echo "== 磁盘 ==" && df -h /)', log)


def get_os_version(log=None):
    """操作系统版本"""
    if IS_MAC:
        return _run('sw_vers', log)
    return _run('(lsb_release -a 2>/dev/null; echo "内核: $(uname -r)")', log)


def get_recent_errors(log=None):
    """最近的系统错误"""
    if IS_MAC:
        return _run('log show --last 1h --style compact --predicate "messageType == 16" 2>/dev/null | tail -30', log)
    return _run('journalctl -p err -n 30 --no-pager 2>/dev/null || sudo journalctl -p err -n 30 --no-pager', log)


def get_installed_software(log=None):
    """已安装软件"""
    if IS_MAC:
        return _run('ls /Applications && echo "== Homebrew ==" && (brew list --formula 2>/dev/null | head -20 || echo 未安装brew)', log)
    return _run('(dpkg -l 2>/dev/null | tail -n +6 | head -50) || (rpm -qa 2>/dev/null | head -50) || '
                '(flatpak list 2>/dev/null)', log)


def get_running_services(log=None):
    """运行中的服务/进程 TOP"""
    if IS_MAC:
        return _run('ps -Ao pid,pcpu,pmem,comm -r | head -25', log)
    return _run('systemctl --type=service --state=running --no-pager 2>/dev/null | head -30', log)


# ==================== 性能优化 ====================

def check_cpu_info(log=None):
    """CPU 信息与负载"""
    if IS_MAC:
        return _run('sysctl -n machdep.cpu.brand_string && sysctl -n hw.ncpu && top -l 1 -n 0 | grep "CPU usage"', log)
    return _run('lscpu | grep -E "Model name|^CPU\\(s\\)" && top -bn1 | head -5', log)


def check_memory_info(log=None):
    """内存信息"""
    if IS_MAC:
        return _run('echo "总内存: $(( $(sysctl -n hw.memsize) / 1073741824 )) GB" && vm_stat | head -8 && memory_pressure | head -6', log)
    return _run('free -h', log)


def check_startup_items(log=None):
    """开机启动项"""
    if IS_MAC:
        return _run('launchctl list | grep -v "com.apple" | head -40', log)
    return _run('systemctl list-unit-files --state=enabled --no-pager 2>/dev/null | head -40', log)


def disable_visual_effects(log=None):
    """减少视觉特效提升流畅度"""
    if IS_MAC:
        return _run('defaults write com.apple.universalaccess reduceTransparency -bool true && '
                    'defaults write com.apple.universalaccess reduceMotion -bool true && '
                    'echo 已开启减弱透明度/动态效果（部分应用需重启生效）', log)
    return _run('gsettings set org.gnome.desktop.interface enable-animations false 2>/dev/null && echo 已关闭桌面动画 || echo 当前桌面环境不支持', log)


def enable_visual_effects(log=None):
    """恢复默认视觉效果"""
    if IS_MAC:
        return _run('defaults write com.apple.universalaccess reduceTransparency -bool false && '
                    'defaults write com.apple.universalaccess reduceMotion -bool false && echo 已恢复默认', log)
    return _run('gsettings set org.gnome.desktop.interface enable-animations true 2>/dev/null && echo 已恢复默认 || echo 当前桌面环境不支持', log)


def purge_memory_mac(log=None):
    """释放非活跃内存（macOS purge）"""
    return _run_admin('purge', log)


def drop_caches_linux(log=None):
    """释放页缓存（Linux，先 sync）"""
    return _run_admin('sync && echo 3 > /proc/sys/vm/drop_caches && echo 缓存已释放', log)


# ==================== 系统工具 ====================

def open_task_manager(log=None):
    """打开系统监视器"""
    if IS_MAC:
        return _run('open -a "Activity Monitor"', log)
    return _run('(gnome-system-monitor || mate-system-monitor || ksysguard || xterm -e top) >/dev/null 2>&1 &', log)


def open_terminal(log=None):
    """打开终端"""
    if IS_MAC:
        return _run('open -a Terminal', log)
    return _run('(x-terminal-emulator || gnome-terminal || konsole || xterm) >/dev/null 2>&1 &', log)


def open_files(log=None):
    """打开文件管理器（用户目录）"""
    if IS_MAC:
        return _run('open ~', log)
    return _run('xdg-open ~ >/dev/null 2>&1 &', log)


def open_settings(log=None):
    """打开系统设置"""
    if IS_MAC:
        return _run('open -a "System Settings" 2>/dev/null || open -a "System Preferences"', log)
    return _run('(gnome-control-center || unity-control-center || systemsettings5) >/dev/null 2>&1 &', log)


def open_network_connections(log=None):
    """打开网络设置"""
    if IS_MAC:
        return _run('open "x-apple.systempreferences:com.apple.Network-Settings.extension" 2>/dev/null || '
                    'open /System/Library/PreferencePanes/Network.prefPane', log)
    return _run('(nm-connection-editor || gnome-control-center network) >/dev/null 2>&1 &', log)


# ==================== 平台专属健康检查 ====================

def check_gateway_connectivity(log=None):
    """检测默认网关和公共网络连通性。"""
    if IS_MAC:
        cmd = ('gw=$(route -n get default 2>/dev/null | awk \'/gateway:/{print $2}\'); '
               'echo "== 默认网关: $gw =="; [ -n "$gw" ] && ping -c 3 -W 1000 "$gw"; '
               'echo "== 公共网络 =="; ping -c 3 -W 1000 1.1.1.1')
    else:
        cmd = ('gw=$(ip route | awk \'/default/{print $3; exit}\'); '
               'echo "== 默认网关: $gw =="; [ -n "$gw" ] && ping -c 3 -W 1 "$gw"; '
               'echo "== 公共网络 =="; ping -c 3 -W 1 1.1.1.1')
    return _run(cmd, log)


def check_dns_resolution(log=None):
    """对比系统 DNS 与当前解析结果。"""
    if IS_MAC:
        return _run('echo "== 系统解析 ==" && dscacheutil -q host -a name example.com && '
                    'echo "== DNS 配置 ==" && scutil --dns | grep nameserver | head -10', log)
    return _run('echo "== 系统解析 ==" && getent ahosts example.com | head -6 && '
                'echo "== DNS 配置 ==" && (resolvectl status 2>/dev/null || cat /etc/resolv.conf)', log)


def list_listening_ports(log=None):
    """查看本机监听端口与对应进程。"""
    if IS_MAC:
        return _run('lsof -nP -iTCP -sTCP:LISTEN | head -80', log)
    return _run('(ss -lntup || netstat -lntup) 2>/dev/null | head -80', log)


def check_disk_layout(log=None):
    """查看磁盘、文件系统与挂载点。"""
    if IS_MAC:
        return _run('diskutil list && echo "== 系统卷 ==" && diskutil info / | '
                    'grep -E "Volume Name|File System|Disk Size|Container Free|SMART Status|Read-Only"', log)
    return _run('lsblk -o NAME,TYPE,FSTYPE,SIZE,FSAVAIL,FSUSE%,MOUNTPOINTS,MODEL && '
                'echo "== 挂载点 ==" && findmnt -D', log)


def verify_system_volume_mac(log=None):
    return _run('diskutil verifyVolume /', log)


def check_apfs_snapshots_mac(log=None):
    return _run('tmutil listlocalsnapshots /', log)


def check_smart_linux(log=None):
    return _run('if command -v smartctl >/dev/null; then '
                'for d in $(smartctl --scan-open | awk \'{print $1}\'); do echo "== $d =="; smartctl -H "$d"; done; '
                'else echo "未安装 smartmontools，可通过系统包管理器安装"; fi', log)


def check_filevault_mac(log=None):
    return _run('fdesetup status', log)


def check_gatekeeper_mac(log=None):
    return _run('spctl --status && echo "== SIP ==" && csrutil status', log)


def check_firewall_mac(log=None):
    return _run('/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate && '
                '/usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode', log)


def check_firewall_linux(log=None):
    return _run('if command -v ufw >/dev/null; then ufw status verbose; '
                'elif command -v firewall-cmd >/dev/null; then firewall-cmd --state; firewall-cmd --list-all; '
                'elif command -v nft >/dev/null; then nft list ruleset; '
                'else echo "未检测到 ufw、firewalld 或 nftables"; fi', log)


def check_failed_logins_linux(log=None):
    return _run_admin('(lastb -n 30 2>/dev/null || journalctl -u ssh -p warning -n 60) | head -60', log)


def check_time_machine_mac(log=None):
    return _run('tmutil status; echo "== 最近备份 =="; tmutil latestbackup 2>/dev/null || echo 暂无可用备份', log)


def check_software_updates_mac(log=None):
    return _run('softwareupdate --list', log)


def brew_doctor_mac(log=None):
    return _run('if command -v brew >/dev/null; then brew doctor; echo "== 可更新包 =="; brew outdated; '
                'else echo "未安装 Homebrew"; fi', log)


def check_package_updates_linux(log=None):
    cmd = ('if command -v apt >/dev/null; then apt list --upgradable 2>/dev/null; '
           'elif command -v dnf >/dev/null; then dnf check-update; '
           'elif command -v pacman >/dev/null; then pacman -Qu; '
           'elif command -v zypper >/dev/null; then zypper list-updates; '
           'else echo "未识别当前发行版的包管理器"; fi')
    return _run(cmd, log)


def repair_packages_linux(log=None):
    cmd = ('if command -v apt-get >/dev/null; then dpkg --configure -a && apt-get -f install -y; '
           'elif command -v dnf >/dev/null; then dnf check && dnf distro-sync -y; '
           'elif command -v pacman >/dev/null; then pacman -Dk; '
           'else echo "当前包管理器没有预设修复流程"; exit 1; fi')
    return _run_admin(cmd, log)


def check_launch_agents_mac(log=None):
    return _run('echo "== 用户 LaunchAgents =="; ls -1 ~/Library/LaunchAgents 2>/dev/null; '
                'echo "== 系统 LaunchAgents/Daemons =="; '
                'ls -1 /Library/LaunchAgents /Library/LaunchDaemons 2>/dev/null | head -100', log)


def check_failed_services_linux(log=None):
    return _run('systemctl --failed --no-pager && echo "== 用户服务 ==" && systemctl --user --failed --no-pager', log)


def analyze_boot_linux(log=None):
    return _run('systemd-analyze 2>/dev/null; echo "== 慢启动单元 TOP20 =="; '
                'systemd-analyze blame 2>/dev/null | head -20; echo "== 本次启动错误 =="; '
                'journalctl -b -p err --no-pager | tail -60', log)


def restart_audio_mac(log=None):
    return _run_admin('killall coreaudiod', log)


def restart_audio_linux(log=None):
    return _run('systemctl --user restart pipewire.service pipewire-pulse.service 2>/dev/null '
                '|| pulseaudio -k; echo 音频服务已请求重启', log)


def check_battery_health(log=None):
    if IS_MAC:
        return _run('system_profiler SPPowerDataType | grep -E "Cycle Count|Condition|Maximum Capacity|State of Charge"', log)
    return _run('if command -v upower >/dev/null; then '
                'upower -i $(upower -e | grep BAT | head -1) | grep -E "state|energy-full|capacity|percentage|time to"; '
                'elif command -v acpi >/dev/null; then acpi -V; else echo "未检测到电池信息工具"; fi', log)


def check_thermal_state(log=None):
    if IS_MAC:
        return _run('pmset -g therm && echo "== 电源状态 ==" && pmset -g batt', log)
    return _run('if command -v sensors >/dev/null; then sensors; '
                'else for z in /sys/class/thermal/thermal_zone*/temp; do [ -r "$z" ] && '
                'echo "$z: $(awk \'{printf "%.1f C", $1/1000}\' "$z")"; done; fi', log)
