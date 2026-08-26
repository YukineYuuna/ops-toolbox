#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""系统工具快捷入口 - 打开常用的 Windows 系统管理工具"""
import subprocess
import os


def open_task_manager(log=None):
    """打开任务管理器"""
    subprocess.run("taskmgr", shell=True)
    if log:
        log("已打开任务管理器")
    return True


def open_event_viewer(log=None):
    """打开事件查看器"""
    subprocess.run("eventvwr", shell=True)
    if log:
        log("已打开事件查看器")
    return True


def open_registry_editor(log=None):
    """打开注册表编辑器"""
    subprocess.run("regedit", shell=True)
    if log:
        log("已打开注册表编辑器")
    return True


def open_services(log=None):
    """打开服务管理"""
    subprocess.run("services.msc", shell=True)
    if log:
        log("已打开服务管理")
    return True


def open_disk_management(log=None):
    """打开磁盘管理"""
    subprocess.run("diskmgmt.msc", shell=True)
    if log:
        log("已打开磁盘管理")
    return True


def open_device_manager(log=None):
    """打开设备管理器"""
    subprocess.run("devmgmt.msc", shell=True)
    if log:
        log("已打开设备管理器")
    return True


def open_network_connections(log=None):
    """打开网络连接"""
    subprocess.run("ncpa.cpl", shell=True)
    if log:
        log("已打开网络连接")
    return True


def open_system_properties(log=None):
    """打开系统属性"""
    subprocess.run("sysdm.cpl", shell=True)
    if log:
        log("已打开系统属性")
    return True


def open_firewall(log=None):
    """打开 Windows Defender 防火墙"""
    subprocess.run("firewall.cpl", shell=True)
    if log:
        log("已打开防火墙设置")
    return True


def open_power_options(log=None):
    """打开电源选项"""
    subprocess.run("powercfg.cpl", shell=True)
    if log:
        log("已打开电源选项")
    return True
