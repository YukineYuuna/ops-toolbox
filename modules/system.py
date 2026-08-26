"""系统修复模块 - SFC扫描、DISM修复、磁盘检查、系统还原等"""
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


def sfc_scannow(log=None):
    """系统文件检查器 - 扫描并修复损坏的系统文件"""
    log("正在执行系统文件检查(SFC)，这可能需要几分钟...")
    log("请耐心等待，不要关闭程序...")
    ok, out = run_cmd("sfc /scannow", log)
    if ok:
        if "未发现任何完整性冲突" in out or "did not find any integrity violations" in out.lower():
            log("系统文件完整，未发现问题!")
        else:
            log("SFC已修复损坏的系统文件，请查看详细日志")
            log("详细日志位于: C:\\Windows\\Logs\\CBS\\CBS.log")
    else:
        log("SFC扫描失败，可能需要使用DISM进行修复")
    return ok


def dism_check_health(log=None):
    """DISM检查系统映像健康状态"""
    log("正在检查系统映像健康状态...")
    ok, out = run_cmd("DISM /Online /Cleanup-Image /CheckHealth", log)
    return ok


def dism_scan_health(log=None):
    """DISM扫描系统映像"""
    log("正在扫描系统映像，这可能需要几分钟...")
    ok, out = run_cmd("DISM /Online /Cleanup-Image /ScanHealth", log)
    return ok


def dism_restore_health(log=None):
    """DISM修复系统映像 - 解决SFC无法修复的问题"""
    log("正在修复系统映像(DISM)，这可能需要较长时间...")
    log("请确保网络连接正常，DISM可能需要从Windows Update下载修复文件")
    ok, out = run_cmd("DISM /Online /Cleanup-Image /RestoreHealth", log)
    if ok:
        log("系统映像修复完成!")
    else:
        log("DISM修复失败，可尝试使用Windows安装介质作为修复源")
    return ok


def dism_full_repair(log=None):
    """完整DISM+SFC修复流程"""
    log("========== 开始完整系统修复 ==========")
    log("步骤1: 检查系统映像健康...")
    dism_check_health(log)
    log("步骤2: 扫描系统映像...")
    dism_scan_health(log)
    log("步骤3: 修复系统映像...")
    dism_restore_health(log)
    log("步骤4: 执行SFC扫描...")
    sfc_scannow(log)
    log("========== 系统修复完成 ==========")
    return True


def chkdsk_system_drive(log=None):
    """检查系统盘文件系统错误"""
    log("正在检查C盘文件系统(只读模式)...")
    ok, out = run_cmd("chkdsk C:", log)
    return ok


def chkdsk_fix(log=None):
    """检查并修复磁盘错误(需要在下次重启时执行)"""
    log("正在计划磁盘修复，将在下次重启时执行...")
    log("此操作需要独占磁盘访问，将在重启时进行")
    ok, out = run_cmd('echo Y | chkdsk C: /f /r', log)
    if ok:
        log("磁盘修复已计划，请重启电脑执行修复")
    return ok


def create_restore_point(log=None):
    """创建系统还原点"""
    log("正在创建系统还原点...")
    ps_cmd = 'powershell -Command "Checkpoint-Computer -Description \'运维工具箱-手动还原点\' -RestorePointType MODIFY_SETTINGS"'
    ok, out = run_cmd(ps_cmd, log)
    if ok:
        log("系统还原点创建成功!")
    else:
        log("创建还原点失败，可能系统保护功能未开启")
    return ok


def enable_system_restore(log=None):
    """开启系统还原功能"""
    log("正在开启C盘系统保护...")
    ps_cmd = 'powershell -Command "Enable-ComputerRestore -Drive C:"'
    ok, out = run_cmd(ps_cmd, log)
    if ok:
        log("系统还原已开启!")
    else:
        log("开启系统还原失败")
    return ok


def repair_windows_update(log=None):
    """修复Windows Update组件"""
    log("正在停止Windows Update服务...")
    run_cmd("net stop wuauserv", log)
    run_cmd("net stop cryptSvc", log)
    run_cmd("net stop bits", log)
    run_cmd("net stop msiserver", log)

    log("正在重命名软件分发文件夹...")
    run_cmd("ren C:\\Windows\\SoftwareDistribution SoftwareDistribution.old", log)
    run_cmd("ren C:\\Windows\\System32\\catroot2 Catroot2.old", log)

    log("正在重新启动Windows Update服务...")
    run_cmd("net start wuauserv", log)
    run_cmd("net start cryptSvc", log)
    run_cmd("net start bits", log)
    run_cmd("net start msiserver", log)

    log("Windows Update组件修复完成!")
    return True


def system_info_short(log=None):
    """获取系统基本信息"""
    log("正在获取系统信息...")
    ok, out = run_cmd("systeminfo", log)
    return ok
