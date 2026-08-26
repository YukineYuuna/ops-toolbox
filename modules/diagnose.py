#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智能诊断模块 - 一键检测项 + 向导式问题排查决策树

CHECKS: 只读检测项，每项返回 {'status': 'ok'|'warn'|'error', 'message': str, 'fixes': [tool_id, ...]}
        fixes 引用 modules/data.py 中已有工具的 id，由界面提供修复按钮。
WIZARD: 决策树。问题节点 {'q', 'desc', 'options':[{'label','icon','next'|'action'}]}
        叶子节点 {'leaf': True, 'title', 'desc', 'fixes':[(tool_id, reason)], 'tips':[str]}
"""
import socket
import os

from modules import utils
from modules.platform_detect import IS_WINDOWS, IS_MAC, IS_LINUX


# ==================== 一键检测项（全部只读，不修改系统） ====================

def _result(status, message, fixes=None):
    return {'status': status, 'message': message, 'fixes': fixes or []}


def check_net_internet():
    """互联网连通性：ping 公共 DNS"""
    if utils.check_internet():
        return _result('ok', '互联网连接正常')
    return _result('error', '无法访问互联网（ping 8.8.8.8 失败）',
                   ['release_renew_ip', 'reset_winsock', 'reset_network_full'])


def check_dns_resolve():
    """DNS 解析是否正常"""
    try:
        socket.setdefaulttimeout(4)
        socket.gethostbyname('www.baidu.com')
        return _result('ok', 'DNS 解析正常')
    except Exception:
        return _result('error', 'DNS 解析失败，网页可能打不开',
                       ['flush_dns', 'clean_dns_cache', 'renew_dns_dhcp'])


def check_gateway():
    """默认网关是否可达"""
    try:
        ok, out = utils.run_cmd('ipconfig', None)
        gateway = None
        if ok:
            for line in out.splitlines():
                if '网关' in line or 'Gateway' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        cand = parts[-1].strip()
                        if cand and cand[0].isdigit():
                            gateway = cand
            if gateway:
                ok2, _ = utils.run_cmd('ping -n 1 -w 1200 ' + gateway, None)
                if ok2:
                    return _result('ok', '默认网关 {} 可达'.format(gateway))
                return _result('warn', '默认网关 {} 不通，可能是路由器或网卡问题'.format(gateway),
                               ['release_renew_ip', 'reset_network_full'])
        return _result('warn', '未获取到默认网关，可能没有有效网络连接',
                       ['release_renew_ip', 'reset_network_full'])
    except Exception:
        return _result('warn', '网关检测未完成', [])


def check_disk_space():
    """C 盘剩余空间"""
    for drive, size, used, free, pct in utils.get_disk_usage():
        if drive == 'C:':
            free_gb = free / (1024 ** 3)
            if pct >= 95:
                return _result('error', 'C 盘已用 {:.0f}%，仅剩 {:.1f} GB，急需清理'.format(pct, free_gb),
                               ['clean_temp_files', 'clean_windows_update_cache', 'full_cleanup', 'scan_large_files'])
            if pct >= 85:
                return _result('warn', 'C 盘已用 {:.0f}%，剩余 {:.1f} GB，建议清理'.format(pct, free_gb),
                               ['analyze_disk_usage', 'full_cleanup', 'scan_large_files'])
            return _result('ok', 'C 盘空间充足（已用 {:.0f}%，剩余 {:.1f} GB）'.format(pct, free_gb))
    return _result('warn', '未检测到 C 盘信息', [])


def check_memory_pressure():
    """内存占用"""
    total, used, pct = utils.get_memory_usage()
    if pct is None:
        return _result('warn', '未能读取内存信息', [])
    if pct >= 90:
        return _result('warn', '内存占用 {:.0f}%，偏高，建议关闭部分程序或检查虚拟内存'.format(pct),
                       ['check_memory_info', 'set_virtual_memory_auto'])
    return _result('ok', '内存占用 {:.0f}%，正常'.format(pct))


def check_disk_smart():
    """硬盘 SMART 健康状态"""
    ok, out = utils.run_cmd('wmic diskdrive get status', None)
    if not ok:
        return _result('warn', '未能读取硬盘 SMART 状态', ['check_disk_performance'])
    bad = [line.strip() for line in out.splitlines()
           if line.strip() and line.strip() not in ('Status', 'OK') and 'Pred' not in line]
    if bad:
        return _result('error', '硬盘健康状态异常（{}），请尽快备份数据'.format(' / '.join(bad[:3])),
                       ['check_disk_performance', 'chkdsk_system_drive'])
    return _result('ok', '硬盘 SMART 状态正常')


def check_recent_critical_errors():
    """最近 24 小时系统严重错误数量"""
    cmd = ('wevtutil qe System '
           '"/q:*[System[(Level=1 or Level=2) and TimeCreated[timediff(@SystemTime) <= 86400000]]]" '
           '/c:40 /rd:true /f:text')
    ok, out = utils.run_cmd(cmd, None)
    if not ok:
        # 没有匹配事件时 wevtutil 会返回错误码并提示找不到事件
        return _result('ok', '最近 24 小时无系统严重错误记录')
    count = out.count('Event[')
    if count >= 20:
        return _result('error', '最近 24 小时有 {}+ 条系统严重错误，建议排查'.format(count),
                       ['get_recent_errors', 'sfc_scannow', 'dism_full_repair'])
    if count >= 5:
        return _result('warn', '最近 24 小时有 {} 条系统严重错误'.format(count),
                       ['get_recent_errors', 'sfc_scannow'])
    if count > 0:
        return _result('ok', '最近 24 小时有 {} 条系统严重错误，数量正常'.format(count))
    return _result('ok', '最近 24 小时无系统严重错误记录')


def check_windows_update_service():
    """Windows Update 服务状态"""
    ok, out = utils.run_cmd('sc query wuauserv', None)
    if not ok:
        return _result('warn', '未能查询 Windows Update 服务', [])
    if 'STOPPED' in out:
        return _result('warn', 'Windows Update 服务未运行，更新可能失败',
                       ['repair_windows_update'])
    return _result('ok', 'Windows Update 服务运行正常')


def check_pending_reboot():
    """是否存在挂起的重启（更新/组件安装未完成）"""
    ok, _ = utils.run_cmd(
        'reg query "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending"',
        None)
    if ok:
        return _result('warn', '系统有待完成的重启（更新未完全生效），建议重启电脑', [])
    ok2, _ = utils.run_cmd(
        'reg query "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired"',
        None)
    if ok2:
        return _result('warn', 'Windows Update 需要重启才能完成，建议重启电脑', [])
    return _result('ok', '无挂起的重启任务')


CHECKS = [
    {'id': 'net_internet', 'name': '互联网连接', 'icon': '🌐', 'run': check_net_internet},
    {'id': 'dns_resolve', 'name': 'DNS 解析', 'icon': '📡', 'run': check_dns_resolve},
    {'id': 'gateway', 'name': '默认网关', 'icon': '🚪', 'run': check_gateway},
    {'id': 'disk_space', 'name': 'C 盘空间', 'icon': '💾', 'run': check_disk_space},
    {'id': 'memory', 'name': '内存占用', 'icon': '🧠', 'run': check_memory_pressure},
    {'id': 'smart', 'name': '硬盘健康', 'icon': '🩺', 'run': check_disk_smart},
    {'id': 'sys_errors', 'name': '系统错误', 'icon': '⚠️', 'run': check_recent_critical_errors},
    {'id': 'wu_service', 'name': 'Windows 更新', 'icon': '🪟', 'run': check_windows_update_service},
    {'id': 'pending_reboot', 'name': '待重启任务', 'icon': '🔄', 'run': check_pending_reboot},
]


# ==================== 向导式排查决策树 ====================

WIZARD = {
    'root': {
        'q': '你的电脑现在遇到什么状况？',
        'desc': '选择最符合的一项，我会通过几个小问题帮你定位故障',
        'options': [
            {'label': '上不了网 / 网络异常', 'icon': '🌐', 'next': 'net_1'},
            {'label': '电脑很慢、卡顿', 'icon': '🐢', 'next': 'slow_1'},
            {'label': '磁盘 / C 盘空间问题', 'icon': '💾', 'next': 'disk_1'},
            {'label': '开机问题（开不了机 / 黑屏 / 反复重启）', 'icon': '🔌', 'next': 'boot_1'},
            {'label': '系统报错 / 蓝屏 / 程序崩溃', 'icon': '⚠️', 'next': 'crash_1'},
            {'label': 'Windows 更新失败或卡住', 'icon': '🪟', 'next': 'wu_1'},
            {'label': '说不上来，先给电脑全面体检一下', 'icon': '🩺', 'action': 'detect'},
        ],
    },

    # ---------- 网络 ----------
    'net_1': {
        'q': '电脑的网络连接状态是？',
        'desc': '看任务栏右下角的网络图标',
        'options': [
            {'label': 'WiFi / 网线显示未连接（红叉或小地球）', 'icon': '🚫', 'next': 'net_noconn'},
            {'label': '已连接，但完全上不了网', 'icon': '🔌', 'next': 'net_2'},
            {'label': '能上网，但部分网站或软件打不开', 'icon': '🧩', 'next': 'net_partial'},
            {'label': '网络时断时续、不稳定', 'icon': '📶', 'next': 'net_flaky'},
            {'label': '能上网，但网速特别慢', 'icon': '🐌', 'next': 'net_slow'},
        ],
    },
    'net_2': {
        'q': '手机等其他设备连同一个 WiFi，能正常上网吗？',
        'desc': '这能判断问题在电脑还是在路由器/宽带',
        'options': [
            {'label': '其他设备也上不了网', 'icon': '📵', 'next': 'net_router'},
            {'label': '只有这台电脑不行', 'icon': '💻', 'next': 'net_pconly'},
            {'label': '没有别的设备可以试', 'icon': '🤷', 'next': 'net_pconly'},
        ],
    },
    'net_noconn': {
        'leaf': True,
        'title': '网络未连接：先查网卡与链路',
        'desc': '连接都没建立，问题通常在网卡被禁用、驱动异常、飞行模式或路由器。按下面顺序排查：',
        'fixes': [
            ('open_network_connections', '查看网卡是否被禁用，右键启用'),
            ('open_device_manager', '检查网卡驱动是否有黄色感叹号'),
            ('reset_network_full', '以上都正常仍连不上，再做完整网络重置'),
        ],
        'tips': [
            '笔记本先确认没有误触飞行模式 / 无线开关（Fn 快捷键）',
            '有线连接检查网线两端是否插紧、路由器指示灯是否正常',
            '重置网络后需要重启电脑',
        ],
    },
    'net_router': {
        'leaf': True,
        'title': '问题在路由器或宽带，不在电脑',
        'desc': '其他设备也上不了网，说明是路由器/光猫/宽带线路的问题，修电脑没有用。建议：',
        'fixes': [
            ('release_renew_ip', '恢复电脑侧 IP 后等路由器恢复'),
        ],
        'tips': [
            '拔掉光猫和路由器电源，等 30 秒再插回（先光猫后路由器）',
            '观察光猫 LOS/光信号 灯：变红闪烁说明是线路故障，直接报修运营商',
            '宽带欠费也会导致全部设备断网',
        ],
    },
    'net_pconly': {
        'leaf': True,
        'title': '只有本机断网：按顺序尝试网络修复',
        'desc': '其他设备正常，问题锁定在这台电脑的网络配置上。从最安全到最彻底依次尝试，前一步解决了就不用做后面的：',
        'fixes': [
            ('flush_dns', '① 先刷新 DNS 缓存，解决域名解析污染'),
            ('release_renew_ip', '② 重新获取 IP，解决 IP 冲突 / 获取失败'),
            ('renew_dns_dhcp', '③ DNS 改回自动获取，排除手动 DNS 填错'),
            ('reset_winsock', '④ 重置 Winsock，修复协议栈组件（需重启）'),
            ('reset_tcpip', '⑤ 重置 TCP/IP 协议栈（需重启）'),
            ('reset_network_full', '⑥ 都不行就一键网络重置（需重启）'),
        ],
        'tips': [
            '标「需重启」的操作执行后重启电脑再测试',
            '如果用过代理/VPN/加速器，先彻底退出它们再测',
        ],
    },
    'net_partial': {
        'leaf': True,
        'title': '部分网站打不开：多为 DNS 缓存或对方问题',
        'desc': '只有个别网站/软件异常，电脑网络本身基本正常。常见原因是 DNS 缓存污染、浏览器缓存或对方服务器问题：',
        'fixes': [
            ('flush_dns', '刷新系统 DNS 缓存'),
            ('clean_dns_cache', '再次确认 DNS 缓存已清理'),
            ('clean_browser_cache', '清理浏览器缓存后重试'),
        ],
        'tips': [
            '换个浏览器或手机流量试试同一网址：都打不开就是对方网站的问题',
            '可在网卡设置里把 DNS 临时改成 223.5.5.5 / 119.29.29.29 试试',
        ],
    },
    'net_flaky': {
        'leaf': True,
        'title': '网络时断时续：查 IP 冲突、信号与驱动',
        'desc': '频繁掉线常见于 IP 地址冲突、WiFi 信号弱、网卡驱动不稳定：',
        'fixes': [
            ('release_renew_ip', '重新获取 IP，排除地址冲突'),
            ('clear_arp', '清除 ARP 缓存，修复局域网映射错误'),
            ('reset_winsock', '重置协议栈（需重启）'),
            ('open_device_manager', '更新或回滚网卡驱动'),
        ],
        'tips': [
            'WiFi 尽量靠近路由器，或改用 5GHz 频段',
            '网线接触不良也会掉线，换根网线试试',
        ],
    },
    'net_slow': {
        'leaf': True,
        'title': '网速慢：先查后台占用与 DNS',
        'desc': '能上网但慢，先看是不是有程序在后台吃带宽，再优化 DNS：',
        'fixes': [
            ('open_task_manager', '在「进程」页按网络排序，找出占带宽的程序'),
            ('flush_dns', '刷新 DNS，解析慢会拖慢打开网页速度'),
            ('clean_prefetch', '清理预读取文件（顺带提速）'),
        ],
        'tips': [
            '重启路由器能缓解大部分长期运行导致的降速',
            '用 speedtest.cn 测速，若远低于宽带套餐速率请找运营商',
        ],
    },

    # ---------- 卡顿 ----------
    'slow_1': {
        'q': '电脑主要是什么时候卡？',
        'desc': '不同场景的卡顿原因差别很大',
        'options': [
            {'label': '开机启动特别慢，进桌面要等很久', 'icon': '🚀', 'next': 'slow_boot'},
            {'label': '用一段时间后越来越卡', 'icon': '📈', 'next': 'slow_runtime'},
            {'label': '磁盘占用经常 100%，点什么都要等', 'icon': '💿', 'next': 'slow_disk'},
            {'label': '玩游戏 / 用特定软件时卡', 'icon': '🎮', 'next': 'slow_app'},
        ],
    },
    'slow_boot': {
        'leaf': True,
        'title': '开机慢：启动项太多或磁盘老化',
        'desc': '开机慢最常见原因是开机自启程序太多，其次是机械硬盘老化：',
        'fixes': [
            ('check_startup_items', '查看有哪些开机自启程序'),
            ('check_disk_performance', '检查硬盘健康，判断是否老化'),
            ('defrag_analysis', '机械硬盘分析碎片率（SSD 跳过）'),
        ],
        'tips': [
            '任务管理器「启动」页禁用不必要的自启项，效果立竿见影',
            '机械硬盘（HDD）升级固态硬盘（SSD）是提速最明显的方式',
        ],
    },
    'slow_runtime': {
        'leaf': True,
        'title': '越用越卡：内存不足 / 后台过多 / 散热',
        'desc': '用久了变卡通常是内存吃紧、后台程序堆积或过热降频：',
        'fixes': [
            ('check_cpu_info', '查看 CPU 型号与当前负载'),
            ('check_memory_info', '查看内存容量与占用'),
            ('set_virtual_memory_auto', '虚拟内存交给系统自动管理'),
            ('disable_visual_effects', '关闭花哨视觉效果，立刻流畅一些'),
        ],
        'tips': [
            '重启电脑能清空内存泄漏，临时缓解',
            '笔记本摸一下底部：很烫说明散热差，清灰或垫高改善进风',
        ],
    },
    'slow_disk': {
        'leaf': True,
        'title': '磁盘 100%：机械硬盘的典型症状',
        'desc': '磁盘占用长期 100% 多见于机械硬盘老化、后台索引/更新、硬盘坏道：',
        'fixes': [
            ('check_disk_performance', '查看硬盘 SMART 健康状态'),
            ('optimize_ssd', 'SSD 执行 TRIM 优化（机械硬盘跳过）'),
            ('defrag_disk', '机械硬盘做碎片整理（SSD 禁用此项）'),
            ('chkdsk_system_drive', '只读检查 C 盘文件系统错误'),
        ],
        'tips': [
            '先打开任务管理器看是什么进程在读写磁盘',
            '机械硬盘 + 长期 100% ≈ 强烈建议升级 SSD',
        ],
    },
    'slow_app': {
        'leaf': True,
        'title': '特定软件卡：优先电源与驱动',
        'desc': '只有特定软件卡，说明系统整体没问题，重点在性能释放和驱动：',
        'fixes': [
            ('set_high_performance', '切到高性能电源计划，解除功耗限制'),
            ('disable_visual_effects', '关闭系统视觉特效，把资源让给软件'),
            ('open_device_manager', '更新显卡驱动（游戏卡顿的重点）'),
        ],
        'tips': [
            '笔记本记得插电源玩，电池模式下性能会受限',
            '游戏卡先看显卡驱动是不是最新，再看温度是否过高降频',
        ],
    },

    # ---------- 磁盘 ----------
    'disk_1': {
        'q': '磁盘方面遇到什么问题？',
        'desc': '空间不足还是怀疑硬盘本身有故障',
        'options': [
            {'label': 'C 盘快满了 / 提示空间不足', 'icon': '📦', 'next': 'disk_full'},
            {'label': '怀疑硬盘有坏道 / 有异响 / 掉盘', 'icon': '🔊', 'next': 'disk_bad'},
            {'label': 'U 盘 / 移动硬盘读不出来', 'icon': '🔌', 'next': 'disk_usb'},
        ],
    },
    'disk_full': {
        'leaf': True,
        'title': 'C 盘空间不足：先分析再清理',
        'desc': '先看清楚空间都被什么占了，再按安全到激进的顺序清理：',
        'fixes': [
            ('analyze_disk_usage', '① 分析 C 盘各目录占用，找到元凶'),
            ('scan_large_files', '② 扫描大于 100MB 的大文件'),
            ('clean_temp_files', '③ 清理临时文件（最安全）'),
            ('clean_windows_update_cache', '④ 清更新缓存，常能释放几个 GB'),
            ('clean_recycle_bin', '⑤ 清空回收站'),
            ('clean_windows_old', '⑥ 删除旧系统备份 Windows.old（不可恢复）'),
            ('disable_hibernate', '⑦ 关闭休眠，释放与内存等量的空间'),
            ('full_cleanup', '嫌麻烦就一键全面清理'),
        ],
        'tips': [
            '微信/QQ 的聊天文件默认存 C 盘，在软件设置里改到其他盘',
            '以后装软件尽量选 D 盘等非系统盘',
        ],
    },
    'disk_bad': {
        'leaf': True,
        'title': '怀疑硬盘故障：先备份，再检测',
        'desc': '硬盘异响、频繁掉盘、文件莫名损坏都是危险信号。第一要务是备份重要数据，然后检测：',
        'fixes': [
            ('check_disk_performance', '查看 SMART 健康状态'),
            ('chkdsk_system_drive', '只读模式检查文件系统错误'),
            ('chkdsk_fix', '计划下次重启时修复文件系统（需重启）'),
        ],
        'tips': [
            '⚠️ 立刻把重要文件复制到 U 盘/移动硬盘/网盘',
            'SMART 报 Pred Fail 说明硬盘随时可能彻底损坏，尽快更换',
            '机械硬盘咔咔异响时尽量减少通电时间',
        ],
    },
    'disk_usb': {
        'leaf': True,
        'title': '外接盘读不出：换接口、查磁盘管理',
        'desc': 'U 盘/移动硬盘识别不了，按硬件到系统的顺序排查：',
        'fixes': [
            ('open_disk_management', '看磁盘管理里是否出现但没分配盘符'),
            ('open_device_manager', '检查 USB 控制器和磁盘驱动器有无感叹号'),
        ],
        'tips': [
            '换个 USB 接口（优先机箱后置）、换根数据线试试',
            '磁盘管理里能看到但没盘符：右键「更改驱动器号和路径」分配一个',
            '提示需要格式化才能用：先别格式化，数据重要的话用数据恢复软件',
        ],
    },

    # ---------- 开机 ----------
    'boot_1': {
        'q': '开机遇到什么状况？',
        'desc': '注意：引导类修复需要在能进入系统（或 PE 环境）下运行本工具',
        'options': [
            {'label': '完全开不了机 / 提示引导错误（BOOTMGR 等）', 'icon': '🛑', 'next': 'boot_no'},
            {'label': '开机后黑屏，只有鼠标或什么都没有', 'icon': '⬛', 'next': 'boot_black'},
            {'label': '反复自动重启 / 进自动修复死循环', 'icon': '🔁', 'next': 'boot_loop'},
            {'label': '能进系统，但桌面 / 任务栏不显示', 'icon': '🖥️', 'next': 'boot_nodesktop'},
            {'label': '想进安全模式排查问题', 'icon': '🛡️', 'next': 'boot_safemode'},
        ],
    },
    'boot_no': {
        'leaf': True,
        'title': '无法开机：修复引导三件套',
        'desc': '提示 BOOTMGR is missing、0xc000000e 等引导错误时，依次修复 MBR、引导扇区和 BCD。在 PE 或能进系统时运行：',
        'fixes': [
            ('fix_boot_full', '一键修复 MBR + 引导扇区 + BCD（推荐）'),
            ('fix_mbr', '只重写主引导记录'),
            ('rebuild_bcd', '只重建 BCD 引导配置'),
        ],
        'tips': [
            '完全进不了系统时，需要用微 PE 等 PE 系统启动 U 盘再运行修复',
            '修复前建议在 PE 里先备份桌面和文档',
        ],
    },
    'boot_black': {
        'leaf': True,
        'title': '开机黑屏：显卡驱动 / 资源管理器 / 快速启动',
        'desc': '能开机但黑屏，常见原因是显卡驱动异常、资源管理器没起来或快速启动冲突：',
        'fixes': [
            ('fix_black_screen', '综合修复开机黑屏（推荐先试）'),
            ('fix_explorer_startup', '修复桌面/任务栏不显示'),
            ('disable_fast_startup', '关闭快速启动，排除休眠文件冲突'),
        ],
        'tips': [
            '黑屏时按 Ctrl+Shift+Esc 能打开任务管理器，说明系统还活着',
            '安全模式下卸载最近更新的显卡驱动往往有效',
        ],
    },
    'boot_loop': {
        'leaf': True,
        'title': '循环重启：引导配置 / 快速启动 / 更新失败',
        'desc': '开机反复重启或自动修复死循环，通常是引导配置损坏或某次更新没装完：',
        'fixes': [
            ('fix_boot_loop', '综合修复循环重启（推荐先试）'),
            ('disable_fast_startup', '关闭快速启动'),
            ('enable_safe_mode', '进安全模式排查（需重启）'),
        ],
        'tips': [
            '能进安全模式后，卸载最近安装的更新和驱动',
            '回忆一下出问题前是否装过新硬件/新驱动',
        ],
    },
    'boot_nodesktop': {
        'leaf': True,
        'title': '桌面不显示：资源管理器没正常启动',
        'desc': '能进系统但没有桌面图标和任务栏，是 explorer.exe 没启动或启动项损坏：',
        'fixes': [
            ('fix_explorer_startup', '修复资源管理器开机自启（推荐先试）'),
            ('check_startup_items', '检查启动项是否被清理过度'),
        ],
        'tips': [
            '临时办法：Ctrl+Shift+Esc 打开任务管理器 → 文件 → 运行新任务 → 输入 explorer',
        ],
    },
    'boot_safemode': {
        'leaf': True,
        'title': '进入安全模式排查',
        'desc': '安全模式只加载最基本驱动，适合卸载问题驱动/软件、排查蓝屏：',
        'fixes': [
            ('enable_safe_mode', '下次重启进入安全模式（需重启）'),
            ('enable_safe_mode_network', '安全模式但需要联网下载驱动（需重启）'),
            ('disable_safe_mode', '排查完取消安全模式，恢复正常启动'),
        ],
        'tips': [
            '排查完记得用「取消安全模式」，否则会一直进安全模式',
        ],
    },

    # ---------- 报错/蓝屏 ----------
    'crash_1': {
        'q': '系统是怎么个报错法？',
        'desc': '蓝屏、程序崩溃还是系统功能异常',
        'options': [
            {'label': '蓝屏（BSOD，蓝底白字重启）', 'icon': '🟦', 'next': 'crash_bsod'},
            {'label': '某些程序频繁崩溃 / 闪退', 'icon': '💥', 'next': 'crash_app'},
            {'label': '系统功能异常（设置打不开、开始菜单失灵等）', 'icon': '🧩', 'next': 'crash_sysfunc'},
            {'label': '想先看看最近的错误日志', 'icon': '📋', 'next': 'crash_logs'},
        ],
    },
    'crash_bsod': {
        'leaf': True,
        'title': '蓝屏：先定位原因，再修系统文件与内存',
        'desc': '蓝屏多由驱动冲突、内存故障或系统文件损坏引起。先查日志定位方向，再做修复：',
        'fixes': [
            ('get_recent_errors', '查看最近系统错误，定位蓝屏模块'),
            ('memory_diagnostic', '内存诊断，排除内存条故障（需重启）'),
            ('sfc_scannow', '扫描修复系统文件'),
            ('dism_full_repair', 'SFC 修不好就做完整映像修复'),
            ('get_driver_info', '检查驱动列表，更新可疑驱动'),
        ],
        'tips': [
            '记下蓝屏终止代码（如 IRQL_NOT_LESS_OR_EQUAL），搜索它能快速定位',
            '最近装过新硬件/驱动的话，先卸载它试试',
            '内存诊断报错基本确定是内存条问题，拔插或更换',
        ],
    },
    'crash_app': {
        'leaf': True,
        'title': '程序崩溃：查日志 + 修系统运行库',
        'desc': '特定程序频繁崩溃，先看错误日志确认模块，再修复系统组件：',
        'fixes': [
            ('get_application_errors', '查看最近应用崩溃记录'),
            ('sfc_scannow', '修复可能被损坏的系统文件'),
            ('dism_check_health', '检查系统映像健康度'),
        ],
        'tips': [
            '只有某一个软件崩溃：重装该软件、安装最新版运行库（VC++/DirectX/.NET）',
            '所有软件都偶尔崩溃：重点查内存和硬盘',
        ],
    },
    'crash_sysfunc': {
        'leaf': True,
        'title': '系统功能异常：修复系统映像',
        'desc': '设置/开始菜单/任务栏等系统组件失灵，多数是系统映像损坏，按彻底程度递增修复：',
        'fixes': [
            ('create_restore_point', '先建个还原点保底'),
            ('sfc_scannow', '① 先跑 SFC 系统文件检查'),
            ('dism_full_repair', '② 再不行做完整 SFC+DISM 修复'),
        ],
        'tips': [
            '如果刚好是某次更新后才异常，可在设置里卸载那次的更新',
            '都修不好还有终极大招：设置 → 系统 → 恢复 → 重置此电脑（保留文件）',
        ],
    },
    'crash_logs': {
        'leaf': True,
        'title': '查看错误日志定位问题',
        'desc': '日志是排查问题的第一手资料，按需要查看：',
        'fixes': [
            ('get_recent_errors', '最近系统级错误（蓝屏/服务崩溃）'),
            ('get_application_errors', '最近应用程序崩溃记录'),
            ('open_event_viewer', '打开事件查看器看完整日志'),
        ],
        'tips': [
            '重点看「错误」级别里反复出现的来源（Source）和事件 ID',
            '把事件 ID + 来源拿去搜索，通常能找到具体解决方案',
        ],
    },

    # ---------- Windows 更新 ----------
    'wu_1': {
        'q': '更新遇到什么问题？',
        'desc': '失败、卡住还是想查已安装的更新',
        'options': [
            {'label': '更新一直失败 / 报错误代码', 'icon': '❌', 'next': 'wu_fail'},
            {'label': '更新卡住不动 / 一直转圈', 'icon': '⏳', 'next': 'wu_stuck'},
            {'label': '想看看已经装了哪些更新', 'icon': '📜', 'next': 'wu_list'},
        ],
    },
    'wu_fail': {
        'leaf': True,
        'title': '更新失败：重置更新组件',
        'desc': '更新报错误代码（如 0x80070002）通常是更新组件或缓存损坏，按顺序修复：',
        'fixes': [
            ('repair_windows_update', '① 重置 Windows Update 组件（主力修复）'),
            ('clean_windows_update_cache', '② 清理更新缓存后重试'),
            ('sfc_scannow', '③ 修系统文件，排除组件损坏'),
        ],
        'tips': [
            '修完重启电脑再去检查更新',
            '记下错误代码搜索，微软官网有对应补丁的离线安装包',
        ],
    },
    'wu_stuck': {
        'leaf': True,
        'title': '更新卡住：重置组件 + 清缓存',
        'desc': '更新进度长时间不动（超过 1 小时），多半是更新服务卡死：',
        'fixes': [
            ('repair_windows_update', '重置更新服务与组件'),
            ('clean_windows_update_cache', '清掉卡住的下载缓存'),
        ],
        'tips': [
            '先确认是真的卡住：硬盘灯还在闪就再等等',
            '重启一次电脑有时就能让卡住的更新继续',
        ],
    },
    'wu_list': {
        'leaf': True,
        'title': '已安装的更新',
        'desc': '查看系统补丁安装情况：',
        'fixes': [
            ('get_hotfix_info', '列出已安装的补丁和更新'),
        ],
        'tips': [
            '怀疑某次更新导致问题，可记下它的 KB 编号到设置里卸载',
        ],
    },
}

WIZARD_ROOT = 'root'


# ==================== macOS / Linux 检测项 ====================

def check_gateway_unix():
    """默认网关是否可达（Unix）"""
    try:
        if IS_MAC:
            ok, out = utils.run_cmd("route -n get default 2>/dev/null | awk '/gateway/{print $2; exit}'", None)
        else:
            ok, out = utils.run_cmd("ip route 2>/dev/null | awk '/default/{print $3; exit}'", None)
        gateway = out.strip().splitlines()[0].strip() if ok and out.strip() else None
        if not gateway:
            return _result('warn', '未获取到默认网关，可能没有有效网络连接', ['release_renew_ip'])
        ok2, _ = utils.run_cmd('ping -c 1 ' + gateway, None)
        if ok2:
            return _result('ok', '默认网关 {} 可达'.format(gateway))
        return _result('warn', '默认网关 {} 不通，可能是路由器或网卡问题'.format(gateway), ['release_renew_ip'])
    except Exception:
        return _result('warn', '网关检测未完成', [])


def check_disk_space_unix():
    """根分区剩余空间"""
    for drive, size, used, free, pct in utils.get_disk_usage():
        free_gb = free / (1024 ** 3)
        if pct >= 95:
            return _result('error', '磁盘已用 {:.0f}%，仅剩 {:.1f} GB，急需清理'.format(pct, free_gb),
                           ['clean_temp_files', 'full_cleanup', 'scan_large_files'])
        if pct >= 85:
            return _result('warn', '磁盘已用 {:.0f}%，剩余 {:.1f} GB，建议清理'.format(pct, free_gb),
                           ['analyze_disk_usage', 'full_cleanup', 'scan_large_files'])
        return _result('ok', '磁盘空间充足（已用 {:.0f}%，剩余 {:.1f} GB）'.format(pct, free_gb))
    return _result('warn', '未检测到磁盘信息', [])


def check_memory_pressure_unix():
    """内存占用（Unix）"""
    total, used, pct = utils.get_memory_usage()
    if pct is None:
        return _result('warn', '未能读取内存信息', [])
    mem_fix = 'purge_memory_mac' if IS_MAC else 'drop_caches_linux'
    if pct >= 90:
        return _result('warn', '内存占用 {:.0f}%，偏高，建议关闭部分程序或释放缓存'.format(pct),
                       ['check_memory_info', mem_fix])
    return _result('ok', '内存占用 {:.0f}%，正常'.format(pct))


def check_recent_errors_unix():
    """系统错误日志数量（Unix）"""
    if IS_LINUX:
        ok, out = utils.run_cmd('journalctl -p err --since "24 hours ago" --no-pager -q 2>/dev/null | wc -l', None)
        window = '24 小时'
        high = 50
    else:
        ok, out = utils.run_cmd('log show --last 1h --style compact --predicate "messageType == 16" 2>/dev/null | wc -l', None)
        window = '1 小时'
        high = 30
    if not ok:
        return _result('warn', '未能读取系统日志', [])
    try:
        count = int(out.strip().splitlines()[0])
    except Exception:
        count = 0
    if count >= high:
        return _result('warn', '最近 {} 有 {} 条系统错误日志，建议排查'.format(window, count), ['get_recent_errors'])
    return _result('ok', '最近 {} 系统错误 {} 条，正常'.format(window, count))


def check_reboot_required_linux():
    """Debian/Ubuntu 待重启标记"""
    if os.path.exists('/var/run/reboot-required'):
        return _result('warn', '有更新需要重启才能生效，建议重启电脑', [])
    return _result('ok', '无待重启任务')


def check_net_internet_unix():
    if utils.check_internet():
        return _result('ok', '互联网连接正常')
    return _result('error', '无法访问互联网（ping 8.8.8.8 失败）', ['release_renew_ip', 'reset_network_full'])


def check_dns_resolve_unix():
    try:
        socket.setdefaulttimeout(4)
        socket.gethostbyname('www.baidu.com')
        return _result('ok', 'DNS 解析正常')
    except Exception:
        return _result('error', 'DNS 解析失败，网页可能打不开', ['flush_dns'])


_CHECK_UNIX = [
    {'id': 'net_internet', 'name': '互联网连接', 'icon': '🌐', 'run': check_net_internet_unix},
    {'id': 'dns_resolve', 'name': 'DNS 解析', 'icon': '📡', 'run': check_dns_resolve_unix},
    {'id': 'gateway', 'name': '默认网关', 'icon': '🚪', 'run': check_gateway_unix},
    {'id': 'disk_space', 'name': '磁盘空间', 'icon': '💾', 'run': check_disk_space_unix},
    {'id': 'memory', 'name': '内存占用', 'icon': '🧠', 'run': check_memory_pressure_unix},
    {'id': 'sys_errors', 'name': '系统错误', 'icon': '⚠️', 'run': check_recent_errors_unix},
]
if IS_LINUX:
    _CHECK_UNIX.append({'id': 'pending_reboot', 'name': '待重启任务', 'icon': '🔄', 'run': check_reboot_required_linux})


def get_checks():
    """按平台返回检测项列表"""
    return CHECKS if IS_WINDOWS else _CHECK_UNIX


# ==================== 向导树的 Unix 覆盖（替换 Windows 专属叶子） ====================

UNIX_LEAF_OVERRIDES = {
    'boot_no': {
        'leaf': True,
        'title': '无法开机：文件系统与引导检查',
        'desc': 'mac/Linux 无法开机多与磁盘文件系统或引导加载器（GRUB）有关：',
        'fixes': [],
        'tips': [
            'macOS：开机按住 Cmd+R 进恢复模式，用「磁盘工具 → 急救」修复磁盘',
            'Linux：用 Live USB 启动，fsck 检查分区，必要时重装/修复 GRUB',
            '修复前先用恢复模式或 Live U 盘备份重要数据',
        ],
    },
    'boot_black': {
        'leaf': True,
        'title': '开机黑屏：显示服务 / 显卡驱动',
        'desc': '能开机但黑屏，常见原因是显示服务没起来或显卡驱动异常：',
        'fixes': [],
        'tips': [
            'macOS：重置 NVRAM（开机按 Cmd+Option+P+R），再重置 SMC',
            'Linux：按 Ctrl+Alt+F3 切到 tty 能登录，说明显示管理器/显卡驱动问题，重装显示管理器或显卡驱动',
            '外接显示器测试，排除屏幕本身故障',
        ],
    },
    'boot_loop': {
        'leaf': True,
        'title': '循环重启：回退内核 / 安全模式',
        'desc': '反复重启通常是某次更新或驱动导致：',
        'fixes': [],
        'tips': [
            'macOS：开机按住 Shift 进安全模式，卸载最近装的软件/驱动',
            'Linux：GRUB 菜单选择旧版本内核启动，回退最近的更新',
            '回忆出问题前装过什么，优先卸载它',
        ],
    },
    'boot_nodesktop': {
        'leaf': True,
        'title': '桌面不显示：桌面环境 / Finder 未启动',
        'desc': '能登录但没有桌面，是桌面环境进程没起来：',
        'fixes': [
            ('open_terminal', '打开终端执行下方命令'),
        ],
        'tips': [
            'macOS：终端执行 killall Finder 重启访达',
            'Linux：Ctrl+Alt+F3 登录 tty，执行 sudo systemctl restart gdm（或 sddm/lightdm）',
        ],
    },
    'boot_safemode': {
        'leaf': True,
        'title': '进入安全模式 / 恢复模式排查',
        'desc': '最小化环境启动，适合卸载问题驱动和软件：',
        'fixes': [],
        'tips': [
            'macOS：开机按住 Shift 进安全模式；Apple 芯片长按电源键进恢复模式',
            'Linux：GRUB 菜单选择 recovery mode（恢复模式）',
        ],
    },
    'wu_fail': {
        'leaf': True,
        'title': '系统更新失败：用包管理器修复',
        'desc': 'mac/Linux 更新失败一般用命令行修复最直接：',
        'fixes': [
            ('open_terminal', '打开终端执行下方命令'),
        ],
        'tips': [
            'macOS：softwareupdate -l 列出更新，sudo softwareupdate -i -a 安装全部',
            'Debian/Ubuntu：sudo apt update && sudo apt -f install 修复依赖',
            'Arch：sudo pacman -Syu 前先看官网新闻有没有需要手动干预的更新',
        ],
    },
    'wu_stuck': {
        'leaf': True,
        'title': '更新卡住：清缓存重试',
        'desc': '更新长时间不动，清掉包管理器缓存再试：',
        'fixes': [
            ('open_terminal', '打开终端执行下方命令'),
        ],
        'tips': [
            'Debian/Ubuntu：sudo apt clean && sudo apt update 后重试',
            'macOS：删掉 /Library/Updates 后重新检查更新',
            '先确认是真卡住：硬盘/网络还有活动就再等等',
        ],
    },
    'wu_list': {
        'leaf': True,
        'title': '已安装的更新 / 软件',
        'desc': '查看系统里已安装的软件包：',
        'fixes': [
            ('get_installed_software', '查看已安装软件列表'),
        ],
        'tips': [
            'macOS：softwareupdate --history 查看更新历史',
            'Debian/Ubuntu：apt list --installed 或 grep " install " /var/log/dpkg.log',
        ],
    },
    'crash_bsod': {
        'leaf': True,
        'title': '系统崩溃/死机：查内核日志与内存',
        'desc': 'mac 的内核 panic、Linux 的死机，多由驱动、内存或过热引起：',
        'fixes': [
            ('get_recent_errors', '查看系统错误日志定位原因'),
            ('check_memory_info', '查看内存状态'),
            ('open_terminal', '打开终端深入排查'),
        ],
        'tips': [
            'macOS：「控制台」查看 panic 报告（/Library/Logs/DiagnosticReports）',
            'Linux：journalctl -k -p err 查内核错误；长期死机可跑 memtest86+ 测内存',
            '记录崩溃前在做什么，帮助定位是哪个驱动/软件',
        ],
    },
    'crash_sysfunc': {
        'leaf': True,
        'title': '系统功能异常：重启相关服务',
        'desc': '系统组件失灵，优先重启对应服务或桌面环境：',
        'fixes': [
            ('get_recent_errors', '查看系统错误日志'),
            ('open_terminal', '打开终端执行修复命令'),
        ],
        'tips': [
            'macOS：killall Dock / killall Finder 重启对应组件',
            'Linux：systemctl --user restart 对应服务，或注销重新登录',
            '都不行就重启电脑，能解决大部分组件卡死',
        ],
    },
    'slow_boot': {
        'leaf': True,
        'title': '开机慢：启动项太多或磁盘老化',
        'desc': '开机慢最常见原因是自启程序太多，其次是机械硬盘老化：',
        'fixes': [
            ('check_startup_items', '查看有哪些开机自启项'),
            ('analyze_disk_usage', '检查磁盘使用情况'),
        ],
        'tips': [
            '在系统设置/系统监视器里禁用不必要的自启项，效果立竿见影',
            'macOS：设置 → 通用 → 登录项；Linux：systemd-analyze blame 看启动耗时',
            '机械硬盘（HDD）升级固态硬盘（SSD）是提速最明显的方式',
        ],
    },
    'slow_disk': {
        'leaf': True,
        'title': '磁盘繁忙：查进程读写与磁盘健康',
        'desc': '磁盘长期高占用，先看是什么进程在读写，再查磁盘健康：',
        'fixes': [
            ('open_task_manager', '打开系统监视器查看磁盘活动'),
            ('analyze_disk_usage', '检查磁盘空间与占用'),
        ],
        'tips': [
            'macOS：活动监视器「磁盘」页找读写大户',
            'Linux：sudo iotop 或 iostat -x 2 查磁盘占用；smartctl -a 查健康（需安装 smartmontools）',
            '机械硬盘长期高占用 ≈ 强烈建议升级 SSD',
        ],
    },
}


def get_wizard(existing_ids=None):
    """返回按平台调整后的向导树：
    - Unix 平台用 UNIX_LEAF_OVERRIDES 覆盖 Windows 专属叶子
    - 所有叶子节点的 fixes 裁剪到当前平台实际存在的工具 id"""
    import copy
    tree = copy.deepcopy(WIZARD)
    if not IS_WINDOWS:
        tree.update(copy.deepcopy(UNIX_LEAF_OVERRIDES))
    if existing_ids is not None:
        for node in tree.values():
            if node.get('leaf') and node.get('fixes'):
                node['fixes'] = [f for f in node['fixes'] if f[0] in existing_ids]
    return tree
