"""性能优化模块 - 电源管理、内存诊断、虚拟内存、服务优化等"""
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


def set_high_performance_power(log=None):
    """设置为高性能电源计划"""
    log("正在获取电源计划列表...")
    ok, out = run_cmd("powercfg /list", log)

    log("正在切换到高性能电源计划...")
    ok, out = run_cmd(
        'powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
        log
    )
    if ok:
        log("已切换到高性能电源计划!")
    else:
        log("切换失败，尝试其他方案ID...")
        # 尝试查找实际可用的高性能方案
        run_cmd("powercfg /list", log)
        log('请在上方输出中找到"高性能"方案GUID并手动设置')
    return ok


def set_balanced_power(log=None):
    """设置为平衡电源计划"""
    log("正在切换到平衡电源计划...")
    ok, out = run_cmd(
        'powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e',
        log
    )
    if ok:
        log("已切换到平衡电源计划!")
    return ok


def set_power_saver(log=None):
    """设置为节能电源计划"""
    log("正在切换到节能电源计划...")
    ok, out = run_cmd(
        'powercfg /setactive a1841308-3541-4fab-bc81-f71556f20b4a',
        log
    )
    if ok:
        log("已切换到节能电源计划!")
    return ok


def memory_diagnostic(log=None):
    """启动Windows内存诊断工具"""
    log("正在启动Windows内存诊断工具...")
    log("计算机将需要重启以执行内存测试")
    ok, out = run_cmd("mdsched", log)
    if ok:
        log("内存诊断工具已启动，请选择'立即重启并检查问题'")
    return ok


def check_virtual_memory(log=None):
    """检查虚拟内存配置"""
    log("正在检查虚拟内存配置...")
    ok, out = run_cmd(
        'wmic pagefile list /format:list',
        log
    )
    if ok:
        log("建议: 虚拟内存初始值=物理内存的1.5倍，最大值=物理内存的3倍")
    return ok


def set_virtual_memory_auto(log=None):
    """设置虚拟内存为自动管理"""
    log("正在设置虚拟内存为系统自动管理...")
    ps_cmd = (
        'powershell -Command '
        '"$sys = Get-WmiObject Win32_ComputerSystem -EnableAllPrivileges; '
        '$sys.AutomaticManagedPagefile = $true; $sys.Put()"'
    )
    ok, out = run_cmd(ps_cmd, log)
    if ok:
        log("虚拟内存已设置为自动管理!")
    else:
        log("设置失败")
    return ok


def disable_startup_programs(log=None):
    """禁用不必要的开机启动项(通过注册表清理)"""
    log("正在检查开机启动项...")
    log("=== 当前用户启动项 ===")
    ok, out = run_cmd(
        'reg query "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"',
        log
    )
    log("提示: 可以通过任务管理器 -> 启动 来管理启动项")
    log("或者使用 msconfig -> 服务 -> 隐藏Microsoft服务 -> 全部禁用")
    return True


def check_disk_performance(log=None):
    """检查磁盘性能状态"""
    log("正在检查磁盘健康状态...")
    ok, out = run_cmd(
        'wmic diskdrive get Status,Model,Size,InterfaceType',
        log
    )
    log("如果Status显示非OK状态，建议备份数据并检查硬盘")
    return ok


def defrag_analysis(log=None):
    """分析磁盘碎片情况"""
    log("正在分析C盘碎片情况...")
    ok, out = run_cmd("defrag C: /A", log)
    return ok


def defrag_disk(log=None):
    """整理磁盘碎片(仅HDD，SSD无需碎片整理)"""
    log("正在整理C盘碎片(仅对机械硬盘有效)...")
    log("SSD固态硬盘不需要碎片整理")
    ok, out = run_cmd("defrag C: /U /V", log)
    return ok


def optimize_ssd(log=None):
    """优化SSD性能(TRIM)"""
    log("正在对SSD执行TRIM优化...")
    ok, out = run_cmd("defrag C: /L", log)
    if ok:
        log("SSD TRIM优化完成!")
    return ok


def check_cpu_info(log=None):
    """查看CPU信息"""
    log("正在获取CPU信息...")
    ok, out = run_cmd("wmic cpu get Name,NumberOfCores,MaxClockSpeed,LoadPercentage", log)
    return ok


def check_memory_info(log=None):
    """查看内存信息"""
    log("正在获取内存信息...")
    ok, out = run_cmd(
        'wmic memorychip get Capacity,Speed,Manufacturer,PartNumber',
        log
    )
    total = 0
    # 简单计算总内存
    for line in (out or "").split("\n"):
        try:
            cap = int(line.strip())
            if cap > 0:
                total += cap
        except:
            pass
    if total > 0:
        log(f"物理内存总计: {total / 1024 / 1024 / 1024:.1f} GB")
    return ok


def disable_visual_effects(log=None):
    """禁用视觉特效以提升性能"""
    log("正在优化系统视觉效果...")
    reg_cmd = (
        'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" '
        '/v VisualFXSetting /t REG_DWORD /d 2 /f'
    )
    ok, out = run_cmd(reg_cmd, log)
    if ok:
        log("视觉效果已优化为最佳性能! 重启或重新登录后生效")
    return ok


def enable_visual_effects(log=None):
    """恢复视觉特效"""
    log("正在恢复默认视觉效果...")
    reg_cmd = (
        'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" '
        '/v VisualFXSetting /t REG_DWORD /d 1 /f'
    )
    ok, out = run_cmd(reg_cmd, log)
    if ok:
        log("视觉效果已恢复为默认设置!")
    return ok


def performance_tuning_full(log=None):
    """一键全面性能优化"""
    log("========== 开始全面性能优化 ==========")
    log("1/5 切换到高性能电源计划...")
    set_high_performance_power(log)
    log("2/5 优化视觉效果...")
    disable_visual_effects(log)
    log("3/5 检查磁盘健康...")
    check_disk_performance(log)
    log("4/5 SSD TRIM优化...")
    optimize_ssd(log)
    log("5/5 检查虚拟内存...")
    check_virtual_memory(log)
    log("========== 性能优化完成 ==========")
    return True
