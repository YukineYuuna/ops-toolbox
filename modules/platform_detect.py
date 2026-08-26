#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""平台检测模块 - 判断当前运行平台（Windows / macOS / Linux）"""
import platform

SYSTEM = platform.system()  # 'Windows' | 'Darwin' | 'Linux'
IS_WINDOWS = SYSTEM == 'Windows'
IS_MAC = SYSTEM == 'Darwin'
IS_LINUX = SYSTEM == 'Linux'
IS_UNIX = not IS_WINDOWS

PLATFORM_LABEL = {
    'Windows': 'Windows',
    'Darwin': 'macOS',
    'Linux': 'Linux',
}.get(SYSTEM, SYSTEM)

APP_NAME = '{} 运维工具箱'.format(PLATFORM_LABEL)
