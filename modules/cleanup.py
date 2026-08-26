"""清理工具模块 - 磁盘清理、临时文件、浏览器缓存、Windows更新缓存等"""
import subprocess
import os
import shutil
import glob as glob_mod


def run_cmd(cmd, log_callback=None):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            encoding="gbk", errors="replace"
        )
        output = result.stdout.strip() or result.stderr.strip()
        if log_callback:
            log_callback(output)
        return result.returncode == 0, output
    except Exception as e:
        if log_callback:
            log_callback(f"执行出错: {e}")
        return False, str(e)


def get_size_str(path):
    """获取文件/文件夹大小，返回人类可读的字符串"""
    try:
        if os.path.isfile(path):
            size = os.path.getsize(path)
        else:
            size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        size += os.path.getsize(fp)
                    except:
                        pass
    except:
        return "未知"

    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    else:
        return f"{size / 1024 / 1024 / 1024:.1f} GB"


def clean_temp_files(log=None):
    """清理系统临时文件"""
    total = 0
    temp_paths = [
        os.environ.get("TEMP", ""),
        os.environ.get("TMP", ""),
        "C:\\Windows\\Temp",
    ]

    for temp_path in temp_paths:
        if not temp_path or not os.path.exists(temp_path):
            continue

        log(f"正在清理: {temp_path}")
        count = 0
        for item in os.listdir(temp_path):
            item_path = os.path.join(temp_path, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    count += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                    count += 1
            except Exception:
                pass
        log(f"  已清理 {count} 个项目")

    log("临时文件清理完成!")
    return True


def clean_windows_update_cache(log=None):
    """清理Windows Update缓存 - 可释放大量C盘空间"""
    update_path = "C:\\Windows\\SoftwareDistribution\\Download"
    if not os.path.exists(update_path):
        log("未找到Windows Update缓存目录")
        return True

    size_before = get_size_str(update_path)
    log(f"Windows Update缓存大小: {size_before}")
    log("正在停止Windows Update服务...")
    run_cmd("net stop wuauserv", log)

    log("正在清理Windows Update缓存...")
    count = 0
    try:
        for item in os.listdir(update_path):
            item_path = os.path.join(update_path, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                else:
                    shutil.rmtree(item_path, ignore_errors=True)
                count += 1
            except:
                pass
    except:
        pass

    log("正在启动Windows Update服务...")
    run_cmd("net start wuauserv", log)
    log(f"Windows Update缓存已清理! 清除了 {count} 个项目，原始大小 {size_before}")
    return True


def clean_recycle_bin(log=None):
    """清空回收站"""
    log("正在清空所有回收站...")
    ok, out = run_cmd("rd /s /q C:\\$Recycle.Bin", log)
    # 也清理其他盘符的回收站
    for drive in ["D:", "E:", "F:", "G:"]:
        run_cmd(f"rd /s /q {drive}\\$Recycle.Bin 2>nul", None)
    if ok:
        log("回收站清空完成!")
    return True


def clean_browser_cache(log=None):
    """清理浏览器缓存 (Chrome, Edge, Firefox)"""
    browsers = {
        "Chrome": os.path.join(os.environ.get("LOCALAPPDATA", ""),
                               "Google", "Chrome", "User Data", "Default", "Cache"),
        "Edge": os.path.join(os.environ.get("LOCALAPPDATA", ""),
                             "Microsoft", "Edge", "User Data", "Default", "Cache"),
        "Firefox": None,  # Firefox缓存路径较复杂，用通配符
    }

    for name, cache_path in browsers.items():
        if cache_path and os.path.exists(cache_path):
            log(f"正在清理 {name} 浏览器缓存...")
            count = 0
            for item in os.listdir(cache_path):
                item_path = os.path.join(cache_path, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    else:
                        shutil.rmtree(item_path, ignore_errors=True)
                    count += 1
                except:
                    pass
            log(f"  {name}: 清理了 {count} 个缓存文件")
        elif name == "Firefox":
            # 尝试清理Firefox缓存
            firefox_base = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                                        "Mozilla", "Firefox", "Profiles")
            if os.path.exists(firefox_base):
                for profile in os.listdir(firefox_base):
                    fcache = os.path.join(firefox_base, profile, "cache2")
                    if os.path.exists(fcache):
                        try:
                            shutil.rmtree(fcache, ignore_errors=True)
                            log(f"  Firefox ({profile}): 缓存已清理")
                        except:
                            pass
        else:
            log(f"  {name}: 未安装或无缓存")

    log("浏览器缓存清理完成!")
    return True


def clean_windows_old(log=None):
    """清理Windows.old文件夹(系统大版本升级后的旧系统文件)"""
    old_path = "C:\\Windows.old"
    if os.path.exists(old_path):
        size = get_size_str(old_path)
        log(f"发现Windows.old文件夹，大小: {size}")
        log("正在清理(使用磁盘清理工具)...")
        # 使用cleanmgr或直接删除
        ok, out = run_cmd("cleanmgr /sagerun:1", log)
        # 备用方案: 使用磁盘清理的特定选项
        if not ok:
            log("尝试直接清理...")
            try:
                # 使用takeown和icacls获取权限
                run_cmd(f'takeown /F "{old_path}" /R /D Y', log)
                run_cmd(f'icacls "{old_path}" /grant administrators:F /T', log)
                shutil.rmtree(old_path, ignore_errors=True)
                log("Windows.old已删除!")
            except Exception as e:
                log(f"清理失败: {e}")
    else:
        log("未找到Windows.old文件夹")
    return True


def clean_prefetch(log=None):
    """清理预读取文件"""
    prefetch_path = "C:\\Windows\\Prefetch"
    if os.path.exists(prefetch_path):
        log("正在清理预读取文件...")
        count = 0
        for item in os.listdir(prefetch_path):
            if item.endswith(".pf"):
                try:
                    os.remove(os.path.join(prefetch_path, item))
                    count += 1
                except:
                    pass
        log(f"已清理 {count} 个预读取文件")
    return True


def clean_thumbnail_cache(log=None):
    """清理缩略图缓存"""
    thumb_path = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                              "Microsoft", "Windows", "Explorer")
    log("正在清理缩略图缓存...")
    count = 0
    if os.path.exists(thumb_path):
        for item in os.listdir(thumb_path):
            if "thumbcache" in item.lower():
                try:
                    os.remove(os.path.join(thumb_path, item))
                    count += 1
                except:
                    pass
    log(f"已清理 {count} 个缩略图缓存文件")
    return True


def clean_dns_cache(log=None):
    """清理DNS缓存"""
    log("正在清理DNS缓存...")
    ok, out = run_cmd("ipconfig /flushdns", log)
    if ok:
        log("DNS缓存已刷新!")
    return ok


def clean_event_logs(log=None):
    """清理Windows事件日志"""
    log("正在清理事件日志...")
    logs = ["Application", "Security", "System", "Setup"]
    for evt_log in logs:
        ok, out = run_cmd(f'wevtutil cl "{evt_log}"', log)
        if ok:
            log(f"  {evt_log} 日志已清理")
    return True


def disable_hibernate(log=None):
    """关闭休眠功能 - 可释放hiberfil.sys占用的磁盘空间(大小约等于内存)"""
    log("正在关闭系统休眠功能...")
    log("这将删除 hiberfil.sys 文件，释放与内存大小相当的磁盘空间")
    ok, out = run_cmd("powercfg -h off", log)
    if ok:
        log("休眠功能已关闭，hiberfil.sys已删除，磁盘空间已释放!")
    else:
        log("关闭休眠失败，请以管理员权限运行")
    return ok


def disk_cleanup_wizard(log=None):
    """启动Windows磁盘清理向导"""
    log("正在启动磁盘清理向导...")
    subprocess.Popen("cleanmgr", shell=True)
    log("磁盘清理向导已启动")
    return True


def full_cleanup(log=None):
    """一键全面清理"""
    log("========== 开始全面系统清理 ==========")
    log("1/8 清理DNS缓存...")
    clean_dns_cache(log)
    log("2/8 清理系统临时文件...")
    clean_temp_files(log)
    log("3/8 清理Windows Update缓存...")
    clean_windows_update_cache(log)
    log("4/8 清空回收站...")
    clean_recycle_bin(log)
    log("5/8 清理浏览器缓存...")
    clean_browser_cache(log)
    log("6/8 清理预读取文件...")
    clean_prefetch(log)
    log("7/8 清理缩略图缓存...")
    clean_thumbnail_cache(log)
    log("8/8 清理事件日志...")
    clean_event_logs(log)
    log("========== 全面清理完成 ==========")
    return True


def scan_large_files(log=None):
    """扫描C盘大文件(>100MB)"""
    log("正在扫描C盘大文件(>100MB)，这可能需要1-2分钟...")
    large_files = []
    scan_dirs = ["C:\\Users", "C:\\Windows\\Temp"]

    for scan_dir in scan_dirs:
        if not os.path.exists(scan_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(scan_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    size = os.path.getsize(fp)
                    if size > 100 * 1024 * 1024:  # > 100MB
                        large_files.append((fp, size))
                except:
                    pass
            # 限制扫描深度，避免耗时过长
            if len(large_files) > 100:
                break
        if len(large_files) > 100:
            break

    if large_files:
        large_files.sort(key=lambda x: x[1], reverse=True)
        log(f"发现 {len(large_files)} 个大文件:")
        for fp, size in large_files[:20]:
            log(f"  {get_size_str(fp)} - {fp}")
        if len(large_files) > 20:
            log(f"  ... 以及 {len(large_files) - 20} 个更多文件")
    else:
        log("未找到大文件(>100MB)")
    return True


def clean_registry_backup(log=None):
    """清理注册表备份文件"""
    log("正在清理注册表备份...")
    reg_backup = "C:\\Windows\\System32\\config\\RegBack"
    if os.path.exists(reg_backup):
        try:
            for item in os.listdir(reg_backup):
                try:
                    os.remove(os.path.join(reg_backup, item))
                except:
                    pass
            log("注册表备份已清理")
        except:
            log("清理注册表备份失败")
    else:
        log("未找到注册表备份目录")
    return True


def analyze_disk_usage(log=None):
    """分析C盘磁盘使用情况"""
    log("========== C盘磁盘使用分析 ==========")
    ok, out = run_cmd('wmic logicaldisk where "DeviceID=\'C:\'" get Size,FreeSpace', log)

    # 分析各主要目录大小
    dirs_to_check = [
        "C:\\Windows",
        "C:\\Users",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\ProgramData",
    ]

    for d in dirs_to_check:
        if os.path.exists(d):
            log(f"分析: {d} ...")
            size = get_size_str(d)
            log(f"  {d}: {size}")

    # 检查特殊大文件
    special_files = [
        ("C:\\hiberfil.sys", "休眠文件"),
        ("C:\\pagefile.sys", "页面文件"),
        ("C:\\swapfile.sys", "交换文件"),
    ]
    for fp, desc in special_files:
        if os.path.exists(fp):
            log(f"  {desc}: {get_size_str(fp)}")

    log("========== 分析完成 ==========")
    return True
