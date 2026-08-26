#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公共工具模块 - 被主界面和其他模块复用的通用函数"""
import subprocess
import os
import sys
import ctypes
from datetime import datetime


def run_cmd(cmd, log_callback=None, encoding=None):
    """执行命令并返回结果，通过log_callback实时输出"""
    if encoding is None:
        encoding = "gbk" if os.name == "nt" else "utf-8"
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            encoding=encoding, errors="replace"
        )
        output = result.stdout.strip() or result.stderr.strip()
        if log_callback:
            log_callback(output)
        return result.returncode == 0, output
    except Exception as e:
        if log_callback:
            log_callback(f"执行出错: {e}")
        return False, str(e)


def is_admin():
    """检查是否拥有管理员权限"""
    try:
        if os.name == "nt":
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        return hasattr(os, "geteuid") and os.geteuid() == 0
    except Exception:
        return False


def run_as_admin(argv=None):
    """以管理员身份重新运行当前程序"""
    if argv is None:
        argv = sys.argv
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            " ".join(f'"{arg}"' for arg in argv[1:]), None, 1
        )
        return True
    except Exception:
        return False


def get_cpu_usage():
    """获取CPU当前使用率"""
    try:
        ok, out = run_cmd("wmic cpu get loadpercentage", None)
        if ok:
            for line in out.split("\n"):
                line = line.strip()
                if line and line.isdigit():
                    return int(line)
    except Exception:
        pass
    return None


def _parse_wmic_rows(output):
    """Return WMIC rows keyed by their headers, independent of column order."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if len(lines) < 2:
        return []
    headers = lines[0].split()
    rows = []
    for line in lines[1:]:
        values = line.split()
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values)))
    return rows


def get_memory_usage():
    """获取内存使用情况，返回 (总字节, 已用字节, 使用率)"""
    try:
        ok, out = run_cmd("wmic OS get TotalVisibleMemorySize,FreePhysicalMemory", None)
        if ok:
            rows = _parse_wmic_rows(out)
            if rows:
                total = int(rows[0]['TotalVisibleMemorySize']) * 1024
                free = int(rows[0]['FreePhysicalMemory']) * 1024
                used = max(0, min(total, total - free))
                return total, used, used / total * 100 if total else 0
    except Exception:
        pass
    return None, None, None


def format_bytes(b):
    """将字节转换为人类可读格式"""
    if b is None:
        return "未知"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(b) < 1024.0:
            return f"{b:.1f} {unit}"
        b /= 1024.0
    return f"{b:.1f} PB"


def format_seconds(seconds):
    """将秒数转换为天时分秒"""
    if seconds is None:
        return "未知"
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}天")
    if hours:
        parts.append(f"{hours}小时")
    if minutes:
        parts.append(f"{minutes}分钟")
    if not parts:
        parts.append(f"{seconds}秒")
    return "".join(parts)


def get_disk_usage():
    """获取各磁盘使用情况，返回 [(盘符, 总字节, 已用字节, 可用字节, 使用率%), ...]"""
    result = []
    try:
        ok, out = run_cmd("wmic logicaldisk where \"DriveType=3\" get DeviceID,Size,FreeSpace", None)
        if ok:
            for row in _parse_wmic_rows(out):
                try:
                    drive = row['DeviceID']
                    size = int(row['Size'])
                    free = int(row['FreeSpace'])
                    used = max(0, min(size, size - free))
                    pct = used / size * 100 if size else 0
                    result.append((drive, size, used, free, pct))
                except (KeyError, ValueError):
                    pass
    except Exception:
        pass
    return result


def get_uptime_seconds():
    """获取系统已运行秒数"""
    try:
        ok, out = run_cmd("wmic os get LastBootUpTime", None)
        if ok:
            for line in out.split("\n"):
                line = line.strip()
                if line and not line.startswith("LastBootUpTime"):
                    boot_time = datetime.strptime(line[:14], "%Y%m%d%H%M%S")
                    return (datetime.now() - boot_time).total_seconds()
    except Exception:
        pass
    return None


def check_internet():
    """检查是否能连接互联网"""
    try:
        ok, _ = run_cmd("ping -n 1 -w 1000 8.8.8.8", None)
        return ok
    except Exception:
        return False


def create_restore_point(log=None):
    """创建系统还原点"""
    ps_cmd = (
        'powershell -Command "Checkpoint-Computer '
        '-Description \'运维工具箱-自动还原点\' -RestorePointType MODIFY_SETTINGS"'
    )
    return run_cmd(ps_cmd, log)[0]


def get_os_name():
    """获取操作系统名称"""
    try:
        ok, out = run_cmd("wmic os get Caption", None)
        if ok:
            for line in out.split("\n"):
                line = line.strip()
                if line and not line.startswith("Caption"):
                    return line
    except Exception:
        pass
    return "Windows"


# ==================== macOS / Linux 实现（覆盖上面的 Windows 版本） ====================
from modules.platform_detect import IS_WINDOWS, IS_MAC, IS_LINUX
import shutil
import re

if not IS_WINDOWS:

    def is_admin():
        """Unix 下 root 即为管理员"""
        try:
            return os.geteuid() == 0
        except Exception:
            return False

    def run_as_admin(argv=None):
        """以 root 身份重新运行（mac 弹系统授权框，Linux 用 pkexec）"""
        try:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            script = os.path.join(app_dir, '运维工具箱.py')
            if IS_MAC:
                cmd = 'do shell script "cd \'{}\' && python3 \'{}\'" with administrator privileges'.format(app_dir, script)
                subprocess.Popen(['osascript', '-e', cmd])
                return True
            if IS_LINUX:
                py = sys.executable or 'python3'
                subprocess.Popen(['pkexec', 'env', 'DISPLAY=' + os.environ.get('DISPLAY', ':0'),
                                  py, script], cwd=app_dir)
                return True
        except Exception:
            pass
        return False

    def check_internet():
        """检查是否能连接互联网"""
        try:
            ok, _ = run_cmd("ping -c 1 8.8.8.8", None)
            return ok
        except Exception:
            return False

    def get_cpu_usage():
        """CPU 使用率：各进程 %cpu 求和（近似，封顶 100）"""
        try:
            ok, out = run_cmd("ps -A -o %cpu | awk '{s+=$1} END {print int(s)}'", None)
            if ok:
                val = out.strip().split('\n')[0].strip()
                if val.isdigit():
                    return min(int(val), 100)
        except Exception:
            pass
        return None

    def get_memory_usage():
        """内存使用：返回 (总字节, 已用字节, 使用率)"""
        try:
            if IS_LINUX:
                ok, out = run_cmd("free -b | awk 'NR==2{print $2, $3}'", None)
                if ok:
                    parts = out.strip().split()
                    if len(parts) >= 2:
                        total, used = int(parts[0]), int(parts[1])
                        return total, used, used / total * 100 if total else 0
            if IS_MAC:
                ok_t, out_t = run_cmd("sysctl -n hw.memsize", None)
                total = int(out_t.strip()) if ok_t else 0
                ok_p, out_p = run_cmd("sysctl -n vm.pagesize", None)
                page_size = int(out_p.strip()) if ok_p else 16384
                ok_v, out_v = run_cmd("vm_stat", None)
                free_pages = inactive_pages = 0
                if ok_v:
                    m = re.search(r'Pages free:\s+(\d+)', out_v)
                    if m:
                        free_pages = int(m.group(1))
                    m = re.search(r'Pages inactive:\s+(\d+)', out_v)
                    if m:
                        inactive_pages = int(m.group(1))
                if total:
                    used = total - (free_pages + inactive_pages) * page_size
                    used = max(0, min(used, total))
                    return total, used, used / total * 100
        except Exception:
            pass
        return None, None, None

    def get_disk_usage():
        """根分区使用情况，返回 [('/', 总, 已用, 可用, 使用率%)]"""
        try:
            total, used, free = shutil.disk_usage('/')
            return [('/', total, used, free, used / total * 100 if total else 0)]
        except Exception:
            return []

    def get_uptime_seconds():
        """系统运行秒数"""
        try:
            if IS_LINUX:
                with open('/proc/uptime', 'r') as f:
                    return float(f.read().split()[0])
            if IS_MAC:
                ok, out = run_cmd("sysctl -n kern.boottime", None)
                if ok:
                    m = re.search(r'sec\s*=\s*(\d+)', out)
                    if m:
                        from datetime import datetime as _dt
                        return (_dt.now() - _dt.fromtimestamp(int(m.group(1)))).total_seconds()
        except Exception:
            pass
        return None

    def get_os_name():
        """操作系统名称"""
        try:
            if IS_MAC:
                ok, out = run_cmd("sw_vers -productName", None)
                ok2, out2 = run_cmd("sw_vers -productVersion", None)
                if ok:
                    return '{} {}'.format(out.strip(), out2.strip() if ok2 else '').strip()
            if IS_LINUX:
                ok, out = run_cmd("lsb_release -ds 2>/dev/null", None)
                if ok and out.strip():
                    return out.strip().strip('"')
                if os.path.exists('/etc/os-release'):
                    with open('/etc/os-release', 'r') as f:
                        for line in f:
                            if line.startswith('PRETTY_NAME='):
                                return line.split('=', 1)[1].strip().strip('"')
        except Exception:
            pass
        return 'macOS' if IS_MAC else 'Linux'

    def create_restore_point(log=None):
        """还原点是 Windows 功能，Unix 不支持"""
        if log:
            log('当前系统不支持系统还原点（Windows 专属功能）')
        return False
