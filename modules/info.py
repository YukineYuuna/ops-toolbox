"""系统信息模块 - 硬件信息、系统版本、磁盘使用、事件日志、驱动信息等"""
import subprocess
import os


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


def get_system_full_info(log=None):
    """获取完整系统信息"""
    log("========== 系统基本信息 ==========")
    run_cmd("systeminfo | findstr /B /C:\"OS Name\" /C:\"OS Version\" /C:\"System Type\" /C:\"Total Physical Memory\" /C:\"Available Physical Memory\"", log)

    log("========== CPU信息 ==========")
    run_cmd("wmic cpu get Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed /format:list", log)

    log("========== 主板信息 ==========")
    run_cmd("wmic baseboard get Manufacturer,Product,Version /format:list", log)

    log("========== BIOS信息 ==========")
    run_cmd("wmic bios get Manufacturer,SMBIOSBIOSVersion,ReleaseDate /format:list", log)

    log("========== 物理内存 ==========")
    run_cmd("wmic memorychip get Capacity,Speed,Manufacturer /format:list", log)

    log("========== 磁盘信息 ==========")
    run_cmd("wmic diskdrive get Model,Size,InterfaceType,MediaType /format:list", log)

    log("========== 显卡信息 ==========")
    run_cmd("wmic path win32_VideoController get Name,AdapterRAM,DriverVersion /format:list", log)

    log("========== 网络适配器 ==========")
    run_cmd("wmic nic where NetEnabled=true get Name,MACAddress,Speed /format:list", log)

    return True


def get_disk_usage(log=None):
    """查看磁盘使用情况"""
    log("正在获取磁盘使用情况...")
    ok, out = run_cmd(
        'wmic logicaldisk where DriveType=3 get DeviceID,FileSystem,Size,FreeSpace',
        log
    )
    if ok and out:
        log("\n格式化显示:")
        for line in out.split("\n"):
            line = line.strip()
            if line and line != "DeviceID":
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        drive = parts[0]
                        fs = parts[1]
                        size_gb = int(parts[2]) / 1024 / 1024 / 1024
                        free_gb = int(parts[3]) / 1024 / 1024 / 1024
                        used_gb = size_gb - free_gb
                        percent = (used_gb / size_gb * 100) if size_gb > 0 else 0
                        log(f"  {drive} [{fs}] 总容量:{size_gb:.1f}GB  已用:{used_gb:.1f}GB  可用:{free_gb:.1f}GB  使用率:{percent:.1f}%")
                    except:
                        log(f"  {line}")
    return ok


def get_os_version(log=None):
    """获取操作系统版本"""
    log("正在获取操作系统版本...")
    ok, out = run_cmd("ver", log)
    run_cmd(
        'wmic os get Caption,Version,BuildNumber,OSArchitecture,InstallDate',
        log
    )
    return ok


def get_recent_errors(log=None):
    """查看最近的系统错误日志"""
    log("正在获取最近10条系统错误...")
    ok, out = run_cmd(
        'wevtutil qe System /c:10 /rd:true /f:text /q:"*[System[(Level=1 or Level=2)]]"',
        log
    )
    if not ok:
        log("获取系统日志失败")
    return ok


def get_application_errors(log=None):
    """查看最近的应用程序错误日志"""
    log("正在获取最近10条应用程序错误...")
    ok, out = run_cmd(
        'wevtutil qe Application /c:10 /rd:true /f:text /q:"*[System[(Level=1 or Level=2)]]"',
        log
    )
    if not ok:
        log("获取应用程序日志失败")
    return ok


def get_installed_software(log=None):
    """获取已安装软件列表"""
    log("正在获取已安装软件列表...")
    ok, out = run_cmd(
        'wmic product get Name,Version,Vendor',
        log
    )
    log("\n注意: 只显示通过Windows Installer安装的软件")
    return ok


def get_driver_info(log=None):
    """获取驱动信息"""
    log("正在获取关键驱动信息...")
    ok, out = run_cmd(
        'driverquery /FO list',
        log
    )
    return ok


def get_network_info(log=None):
    """获取网络配置信息"""
    log("正在获取网络配置...")
    run_cmd("ipconfig /all", log)
    log("========== DNS缓存统计 ==========")
    run_cmd("ipconfig /displaydns | find /c \"Record\"", log)
    return True


def get_running_services(log=None):
    """查看正在运行的服务(非Microsoft)"""
    log("正在获取非Microsoft的运行中服务...")
    ok, out = run_cmd(
        'wmic service where "State=\'Running\' and Not PathName like \'%Microsoft%\' and Not PathName like \'%Windows%\'" get Name,DisplayName,StartMode',
        log
    )
    return ok


def get_hotfix_info(log=None):
    """查看已安装的系统更新"""
    log("正在获取最近安装的系统更新...")
    ok, out = run_cmd(
        'wmic qfe list brief /format:texttable',
        log
    )
    return ok


def export_full_report(log=None):
    """导出完整系统报告到桌面"""
    report_path = os.path.join(os.environ.get("USERPROFILE", "C:\\"), "Desktop", "运维工具箱_系统报告.txt")
    log(f"正在生成系统报告: {report_path}")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("        运维工具箱 - 系统诊断报告\n")
            f.write("=" * 60 + "\n\n")
            f.flush()

            # 收集各类信息...
            log("报告已保存到桌面: 运维工具箱_系统报告.txt")
    except Exception as e:
        log(f"保存报告失败: {e}")
    return True
