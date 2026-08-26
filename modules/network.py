"""网络修复模块 - DNS缓存清理、Winsock重置、IP刷新、ARP清理等"""
import subprocess
import re


def run_cmd(cmd, log_callback=None):
    """执行命令并返回结果，通过log_callback实时输出"""
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


def flush_dns(log=None):
    """刷新DNS缓存 - 解决DNS缓存过多/过期导致无法上网"""
    log("正在刷新DNS缓存...")
    ok, out = run_cmd("ipconfig /flushdns", log)
    if ok:
        log("DNS缓存刷新成功!")
    else:
        log("DNS缓存刷新失败，请以管理员权限运行")
    return ok


def release_renew_ip(log=None):
    """释放并更新IP地址"""
    log("正在释放IP地址...")
    run_cmd("ipconfig /release", log)
    log("正在重新获取IP地址...")
    ok, out = run_cmd("ipconfig /renew", log)
    if ok:
        log("IP地址更新成功!")
    return ok


def reset_winsock(log=None):
    """重置Winsock目录 - 解决网络协议栈问题"""
    log("正在重置Winsock目录...")
    ok, out = run_cmd("netsh winsock reset", log)
    if ok:
        log("Winsock重置成功! 需要重启电脑生效")
    return ok


def reset_tcpip(log=None):
    """重置TCP/IP协议栈"""
    log("正在重置TCP/IP协议栈...")
    ok, out = run_cmd("netsh int ip reset", log)
    if ok:
        log("TCP/IP协议栈重置成功! 需要重启电脑生效")
    return ok


def reset_network_full(log=None):
    """一键网络全面重置 - 执行所有网络修复操作"""
    log("========== 开始全面网络重置 ==========")
    log("1/6 刷新DNS缓存...")
    flush_dns(log)
    log("2/6 释放并更新IP地址...")
    release_renew_ip(log)
    log("3/6 重置Winsock目录...")
    reset_winsock(log)
    log("4/6 重置TCP/IP协议栈...")
    reset_tcpip(log)
    log("5/6 清除ARP缓存...")
    clear_arp(log)
    log("6/6 重置Windows防火墙...")
    reset_firewall(log)
    log("========== 网络全面重置完成 ==========")
    log("建议重启电脑使所有更改生效")
    return True


def clear_arp(log=None):
    """清除ARP缓存表"""
    log("正在清除ARP缓存...")
    ok, out = run_cmd("arp -d *", log)
    if ok:
        log("ARP缓存清除成功!")
    return ok


def reset_firewall(log=None):
    """重置Windows防火墙到默认设置"""
    log("正在重置Windows防火墙...")
    ok, out = run_cmd("netsh advfirewall reset", log)
    if ok:
        log("防火墙重置成功!")
    return ok


def renew_dns_dhcp(log=None):
    """将DNS设置为自动获取(DHCP)"""
    log("正在获取网络适配器列表...")
    ok, out = run_cmd('wmic nic where "NetEnabled=true" get NetConnectionID', log)
    if not ok:
        log("无法获取网络适配器列表")
        return False

    # 解析适配器名称
    adapters = []
    for line in out.split("\n"):
        name = line.strip()
        if name and name != "NetConnectionID":
            adapters.append(name)

    if not adapters:
        log("未找到活动的网络适配器")
        return False

    for adapter in adapters:
        log(f"正在为 [{adapter}] 设置DNS为自动获取...")
        run_cmd(f'netsh int ip set dns name="{adapter}" dhcp', log)

    log("DNS已设置为自动获取")
    return True


def flush_dns_and_browser_cache(log=None):
    """刷新DNS并清理浏览器DNS缓存"""
    log("正在刷新系统DNS缓存...")
    flush_dns(log)

    log("正在刷新Chrome DNS缓存...")
    run_cmd('ipconfig /flushdns', log)
    # Chrome内部DNS缓存需要手动清理，这里执行netsh方式
    log("提示: 浏览器内DNS缓存请手动清理 chrome://net-internals/#dns")

    return True
