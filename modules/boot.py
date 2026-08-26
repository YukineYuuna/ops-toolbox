"""开机修复模块 - MBR修复、BCD重建、快速启动管理、启动项管理"""
import subprocess


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


def fix_mbr(log=None):
    """修复主引导记录(MBR) - 解决"Missing operating system"等错误"""
    log("警告: 此操作将重写主引导记录(MBR)")
    log("正在修复MBR...")
    ok, out = run_cmd("bootrec /fixmbr", log)
    if ok:
        log("MBR修复成功!")
    else:
        log("MBR修复失败")
    return ok


def fix_boot(log=None):
    """修复引导扇区 - 解决"BOOTMGR is missing"等错误"""
    log("正在修复引导扇区...")
    ok, out = run_cmd("bootrec /fixboot", log)
    if ok:
        log("引导扇区修复成功!")
    else:
        log("引导扇区修复失败")
    return ok


def rebuild_bcd(log=None):
    """重建BCD引导配置 - 解决系统无法引导的问题"""
    log("正在重建BCD引导配置数据...")
    log("此操作将扫描所有Windows安装并重建引导菜单")
    ok, out = run_cmd("bootrec /rebuildbcd", log)
    if ok:
        log("BCD重建成功!")
    else:
        log("BCD重建失败")
    return ok


def fix_boot_full(log=None):
    """一键完整引导修复"""
    log("========== 开始完整引导修复 ==========")
    log("1/3 修复MBR...")
    fix_mbr(log)
    log("2/3 修复引导扇区...")
    fix_boot(log)
    log("3/3 重建BCD...")
    rebuild_bcd(log)
    log("========== 引导修复完成 ==========")
    log("请重启电脑验证修复结果")
    return True


def disable_fast_startup(log=None):
    """禁用快速启动 - 解决关机后无法正常开机的问题"""
    log("正在禁用快速启动...")
    log("快速启动可能导致关机异常、驱动加载失败等问题")
    # 修改注册表禁用快速启动
    reg_cmd = (
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" '
        '/v HiberbootEnabled /t REG_DWORD /d 0 /f'
    )
    ok, out = run_cmd(reg_cmd, log)
    if ok:
        log("快速启动已禁用! 重启后生效")
    else:
        log("禁用快速启动失败")
    return ok


def enable_fast_startup(log=None):
    """启用快速启动"""
    log("正在启用快速启动...")
    reg_cmd = (
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" '
        '/v HiberbootEnabled /t REG_DWORD /d 1 /f'
    )
    ok, out = run_cmd(reg_cmd, log)
    if ok:
        log("快速启动已启用!")
    else:
        log("启用快速启动失败")
    return ok


def check_startup_items(log=None):
    """查看开机启动项"""
    log("正在获取开机启动项...")
    log("=== 注册表启动项 ===")
    run_cmd(
        'reg query "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"',
        log
    )
    run_cmd(
        'reg query "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"',
        log
    )
    log("=== 启动文件夹 ===")
    run_cmd("dir \"C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\" 2>nul", log)
    run_cmd("dir \"%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\" 2>nul", log)
    log("启动项检查完成")
    return True


def enable_safe_mode_boot(log=None):
    """设置下次启动进入安全模式"""
    log("正在配置安全模式启动...")
    ok, out = run_cmd('bcdedit /set {current} safeboot minimal', log)
    if ok:
        log("已设置下次启动进入安全模式!")
        log("重启后将自动进入安全模式")
    else:
        log("配置失败，请以管理员权限运行")
    return ok


def enable_safe_mode_network(log=None):
    """设置下次启动进入带网络的安全模式"""
    log("正在配置带网络的安全模式启动...")
    ok, out = run_cmd('bcdedit /set {current} safeboot network', log)
    if ok:
        log("已设置下次启动进入带网络的安全模式!")
    return ok


def disable_safe_mode(log=None):
    """取消安全模式，恢复正常启动"""
    log("正在恢复正常启动模式...")
    ok, out = run_cmd('bcdedit /deletevalue {current} safeboot', log)
    if ok:
        log("已恢复正常启动模式!")
    else:
        log("取消失败，可能当前不在安全模式配置中")
    return ok


def check_boot_config(log=None):
    """查看当前引导配置"""
    log("正在获取引导配置...")
    ok, out = run_cmd("bcdedit", log)
    return ok


def fix_black_screen(log=None):
    """修复开机黑屏问题 - 综合处理"""
    log("========== 开机黑屏修复 ==========")
    log("正在执行黑屏修复流程...")
    log("1/5 禁用快速启动...")
    disable_fast_startup(log)
    log("2/5 修复系统文件...")
    run_cmd("sfc /scannow", log)
    log("3/5 修复DISM...")
    run_cmd("DISM /Online /Cleanup-Image /RestoreHealth", log)
    log("4/5 重置显卡驱动...")
    run_cmd(
        'pnputil /restart-device "PCI\\VEN_*" 2>nul',
        log
    )
    log("5/5 检查磁盘错误...")
    run_cmd("chkdsk C: /f", log)
    log("========== 黑屏修复流程完成 ==========")
    log("建议重启电脑检查是否恢复正常")
    return True


def fix_boot_loop(log=None):
    """修复开机循环重启"""
    log("========== 开机循环重启修复 ==========")
    log("1/4 禁用自动重启...")
    run_cmd(
        'wmic recoveros set AutoReboot = False',
        log
    )
    log("2/4 检查系统文件...")
    run_cmd("sfc /scannow", log)
    log("3/4 修复引导...")
    fix_boot_full(log)
    log("4/4 检查磁盘...")
    run_cmd("chkdsk C: /f", log)
    log("========== 修复完成 ==========")
    log("建议重启电脑检查")
    return True


def fix_explorer_startup(log=None):
    """修复资源管理器不自动启动的问题"""
    log("正在修复资源管理器启动问题...")
    reg_cmd = (
        'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon" '
        '/v Shell /t REG_SZ /d explorer.exe /f'
    )
    ok, out = run_cmd(reg_cmd, log)
    if ok:
        log("资源管理器启动配置已修复!")
    return ok
