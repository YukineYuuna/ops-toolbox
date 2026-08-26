#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 运维工具箱 v3.0
MaintenanceToolbox 主类
"""
import sys
import os
import threading
import json
from datetime import datetime
from collections import deque

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

from modules import utils, diagnose
from modules.platform_detect import IS_WINDOWS, IS_MAC, IS_LINUX, APP_NAME

if IS_WINDOWS:
    from modules import data as data_module
elif IS_MAC:
    from modules import data_mac as data_module
else:
    from modules import data_linux as data_module
from modules.ui import SidebarButton, ModernTooltip, ActionCard, GradientBanner

APP_VERSION = 'v3.0'
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, 'toolbox_config.json')

THEMES = {
    'light': {
        'bg': '#e8eef3',
        'fg': '#17212b',
        'card': '#f8fbfd',
        'card_border': '#cbd7e0',
        'card_hover': '#ffffff',
        'panel': '#f2f7fa',
        'panel_border': '#c5d2dc',
        'icon_bg': '#e3f3f0',
        'tag_bg': '#e9eff3',
        'accent': '#168f80',
        'accent_hover': '#0f7469',
        'accent_fg': '#ffffff',
        'banner_end': '#2e7288',
        'sidebar': '#f3f7f9',
        'sidebar_active': '#deebe9',
        'sidebar_hover': '#e8eff3',
        'sidebar_fg': '#52616d',
        'success': '#278a5d',
        'warning': '#b97818',
        'error': '#d34f59',
        'info': '#397fb8',
        'muted': '#647582',
        'log_bg': '#f4f8fa',
        'log_fg': '#22303b',
        'header': '#f7fafc',
        'header_border': '#cbd7e0',
    },
    'dark': {
        'bg': '#0b1016',
        'fg': '#edf4f7',
        'card': '#151e27',
        'card_border': '#273744',
        'card_hover': '#1a2833',
        'panel': '#121a22',
        'panel_border': '#263542',
        'icon_bg': '#1b3133',
        'tag_bg': '#1d2933',
        'accent': '#43c6ac',
        'accent_hover': '#35ab95',
        'accent_fg': '#071512',
        'banner_end': '#257a8a',
        'sidebar': '#10171e',
        'sidebar_active': '#1a2931',
        'sidebar_hover': '#17222b',
        'sidebar_fg': '#8fa0ac',
        'success': '#53ca8c',
        'warning': '#f2b84b',
        'error': '#f16c75',
        'info': '#69aef3',
        'muted': '#8fa0ac',
        'log_bg': '#0d141b',
        'log_fg': '#d6e0e6',
        'header': '#10171e',
        'header_border': '#273744',
    }
}


class MaintenanceToolbox:
    def __init__(self, root):
        self.root = root
        self.root.title(f'{APP_NAME} {APP_VERSION}')
        self.root.geometry('1280x820')
        self.root.minsize(1040, 700)
        self.config = self.load_config()
        self.theme_name = self.config.get('theme', 'dark')
        self.theme = THEMES[self.theme_name]
        self.is_admin = utils.is_admin()
        self.queue_lock = threading.Lock()
        self.queue = deque()
        self.running_task = None
        self.task_thread = None
        self.cancelled = False
        self.current_cards = []
        self.sidebar_buttons = []
        self.functions = data_module.FUNCTIONS
        self.wizard_tree = diagnose.get_wizard({t['id'] for t in self.functions})
        self.stat_cards = {}
        self._refresh_stats_job = None
        self.wizard_history = []
        self.wizard_node = 'root'
        self._detecting = False
        self.detected_fix_ids = []
        self.stat_bars = {}
        self._stats_fetching = False
        self._search_job = None
        self._resize_job = None
        self._last_card_tasks = None
        self._card_cols = 3
        self._closing = False

        self.setup_styles()
        self.build_ui()
        self.bind_shortcuts()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self.show_dashboard()

        self.log(f'欢迎使用 {APP_NAME} {APP_VERSION}', 'title')
        self.log(f"当前权限: {'管理员' if self.is_admin else '普通用户'}", 'info' if self.is_admin else 'warning')
        if not self.is_admin:
            self.log('建议点击右上角 [提升权限] 以管理员身份运行，确保所有功能正常', 'warning')

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {'theme': 'dark', 'favorites': [], 'recent': [], 'auto_backup': True}

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f'保存配置失败: {e}', 'error')

    def _safe_after(self, delay, callback):
        if self._closing:
            return None
        try:
            return self.root.after(delay, callback)
        except (RuntimeError, tk.TclError):
            return None

    def _on_close(self):
        self._closing = True
        for job in (self._refresh_stats_job, self._search_job, self._resize_job):
            if job:
                try:
                    self.root.after_cancel(job)
                except tk.TclError:
                    pass
        self.root.destroy()

    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('Vertical.TScrollbar', background=self.theme['accent'], troughcolor=self.theme['bg'], borderwidth=0)
        style.configure('Horizontal.TProgressbar', background=self.theme['accent'], troughcolor=self.theme['card'], borderwidth=0, lightcolor=self.theme['accent'], darkcolor=self.theme['accent'])
    def build_ui(self):
        self.categories = [
            ('dashboard', '概览', '⌂'),
            ('favorites', '收藏', '★'),
            ('diagnose', '智能诊断', '🩺'),
        ] + list(getattr(data_module, 'CATEGORIES', [
            ('network', '网络修复', '🌐'),
            ('system', '系统修复', '🛠'),
            ('cleanup', '清理工具', '🧹'),
            ('boot', '开机修复', '🔧'),
            ('optimize', '性能优化', '⚡'),
            ('info', '系统信息', '📊'),
            ('tools', '系统工具', '🧰'),
        ]))
        self.current_view = 'dashboard'
        self.root.configure(bg=self.theme['bg'])
        self.main_frame = tk.Frame(self.root, bg=self.theme['bg'])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.build_header()
        self.build_sidebar()
        self.build_content_area()
        self.build_log_panel()

    def build_header(self):
        self.header = tk.Frame(self.main_frame, bg=self.theme['header'], height=54, highlightbackground=self.theme['header_border'], highlightthickness=1)
        self.header.pack(side=tk.TOP, fill=tk.X)
        self.header.pack_propagate(False)
        self.header_logo_lbl = tk.Label(self.header, text='⚙', bg=self.theme['header'], fg=self.theme['accent'], font=('Segoe UI Symbol', 18, 'bold'))
        self.header_logo_lbl.pack(side=tk.LEFT, padx=(18, 8))
        self.header_title_lbl = tk.Label(self.header, text=APP_NAME, bg=self.theme['header'], fg=self.theme['fg'], font=('Microsoft YaHei', 13, 'bold'))
        self.header_title_lbl.pack(side=tk.LEFT)
        tk.Frame(self.header, width=1, bg=self.theme['header_border']).pack(side=tk.LEFT, fill=tk.Y, padx=18, pady=13)
        self.header_nav_items = []
        self._make_header_nav('工作台', '⌂', lambda: self.on_sidebar_click('dashboard'))
        self._make_header_nav('智能诊断', '◇', lambda: self.on_sidebar_click('diagnose'))
        self._make_header_nav('工具目录', '▦', lambda: self.on_sidebar_click('tools'))

        self.backup_var = tk.BooleanVar(value=self.config.get('auto_backup', True))
        self.backup_chk = tk.Checkbutton(self.header, text='自动备份', variable=self.backup_var, bg=self.theme['header'], fg=self.theme['muted'], activebackground=self.theme['header'], activeforeground=self.theme['fg'], selectcolor=self.theme['sidebar_active'], font=('Microsoft YaHei', 8), command=self._on_auto_backup_toggle, bd=0, highlightthickness=0)
        if IS_WINDOWS:
            self.backup_chk.pack(side=tk.RIGHT, padx=(8, 14))
        self.theme_btn = tk.Label(self.header, text=('☀' if self.theme_name == 'light' else '☾'), bg=self.theme['header'], fg=self.theme['muted'], font=('Segoe UI Symbol', 14), cursor='hand2', width=3)
        self.theme_btn.pack(side=tk.RIGHT, padx=2)
        self.theme_btn.bind('<Enter>', lambda e: self.theme_btn.configure(bg=self.theme['sidebar_active']))
        self.theme_btn.bind('<Leave>', lambda e: self.theme_btn.configure(bg=self.theme['header']))
        self.theme_btn.bind('<Button-1>', self.toggle_theme)
        ModernTooltip(self.theme_btn, '切换明暗主题')
        self.export_btn = tk.Label(self.header, text='⇩', bg=self.theme['sidebar_active'], fg=self.theme['info'], font=('Segoe UI Symbol', 12, 'bold'), width=3, pady=3, cursor='hand2')
        self.export_btn.pack(side=tk.RIGHT, padx=3)
        self.export_btn.bind('<Enter>', lambda e: self.export_btn.configure(bg=self.theme['sidebar_hover']))
        self.export_btn.bind('<Leave>', lambda e: self.export_btn.configure(bg=self.theme['sidebar_active']))
        self.export_btn.bind('<Button-1>', self.export_full_report)
        ModernTooltip(self.export_btn, '导出系统报告')
        self.repair_btn = None
        if IS_WINDOWS:
            self.repair_btn = tk.Label(self.header, text='一键修复', bg=self.theme['success'], fg='#071512', font=('Microsoft YaHei', 8, 'bold'), padx=10, pady=4, cursor='hand2')
            self.repair_btn.pack(side=tk.RIGHT, padx=4)
            self.repair_btn.bind('<Enter>', lambda e: self.repair_btn.configure(bg=self.theme['accent_hover']))
            self.repair_btn.bind('<Leave>', lambda e: self.repair_btn.configure(bg=self.theme['success']))
            self.repair_btn.bind('<Button-1>', self.one_click_repair)
        self.elevate_btn = tk.Label(self.header, text='提升权限', bg=self.theme['accent'], fg=self.theme['accent_fg'], font=('Microsoft YaHei', 8, 'bold'), padx=10, pady=4, cursor='hand2')
        self.elevate_btn.pack(side=tk.RIGHT, padx=4)
        self.elevate_btn.bind('<Enter>', lambda e: self.elevate_btn.configure(bg=self.theme['accent_hover']))
        self.elevate_btn.bind('<Leave>', lambda e: self.elevate_btn.configure(bg=self.theme['accent']))
        self.elevate_btn.bind('<Button-1>', self.elevate_privilege)
        self.admin_badge = tk.Label(self.header, text='普通用户', bg=self.theme['tag_bg'], fg=self.theme['warning'], font=('Microsoft YaHei', 8), padx=8, pady=3)
        self.admin_badge.pack(side=tk.RIGHT, padx=(8, 4))
        self.update_admin_badge()

    def _make_header_nav(self, text, icon, command):
        item = tk.Label(self.header, text='{}  {}'.format(icon, text), bg=self.theme['header'], fg=self.theme['muted'], font=('Microsoft YaHei', 9), padx=10, cursor='hand2')
        item.pack(side=tk.LEFT, fill=tk.Y)
        item.bind('<Enter>', lambda event, label=item: label.configure(bg=self.theme['sidebar_hover'], fg=self.theme['fg']))
        item.bind('<Leave>', lambda event, label=item: label.configure(bg=self.theme['header'], fg=self.theme['muted']))
        item.bind('<Button-1>', lambda event: command())
        self.header_nav_items.append(item)

    def build_sidebar(self):
        self.sidebar = tk.Frame(self.main_frame, bg=self.theme['sidebar'], width=196, highlightbackground=self.theme['header_border'], highlightthickness=1)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        self.sidebar_heading = tk.Frame(self.sidebar, bg=self.theme['sidebar'], height=48)
        self.sidebar_heading.pack(side=tk.TOP, fill=tk.X)
        self.sidebar_heading.pack_propagate(False)
        self.sidebar_logo_lbl = tk.Label(self.sidebar_heading, text='▦', bg=self.theme['sidebar'], fg=self.theme['accent'], font=('Segoe UI Symbol', 12, 'bold'))
        self.sidebar_logo_lbl.pack(side=tk.LEFT, padx=(15, 7))
        self.sidebar_title_lbl = tk.Label(self.sidebar_heading, text='功能导航', bg=self.theme['sidebar'], fg=self.theme['fg'], font=('Microsoft YaHei', 10, 'bold'))
        self.sidebar_title_lbl.pack(side=tk.LEFT)

        self.search_frame = tk.Frame(self.sidebar, bg=self.theme['card_border'], height=38)
        self.search_frame.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0, 12))
        self.search_frame.pack_propagate(False)
        self.search_inner = tk.Frame(self.search_frame, bg=self.theme['card'])
        self.search_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.search_icon = tk.Label(self.search_inner, text='⌕', bg=self.theme['card'], fg=self.theme['muted'], font=('Segoe UI Symbol', 13))
        self.search_icon.pack(side=tk.LEFT, padx=(8, 3))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.search_inner, textvariable=self.search_var, bg=self.theme['card'], fg=self.theme['fg'], insertbackground=self.theme['accent'], relief=tk.FLAT, font=('Microsoft YaHei', 9), bd=0)
        self.search_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 7), pady=4)
        self.search_var.trace('w', lambda *args: self._on_search_changed())
        self.cat_frame = tk.Frame(self.sidebar, bg=self.theme['sidebar'])
        self.cat_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.sidebar_buttons = []
        for cat_id, label, icon in self.categories:
            btn = SidebarButton(self.cat_frame, cat_id, label, icon, lambda c=cat_id: self.on_sidebar_click(c), self.theme, active=(cat_id == 'dashboard'))
            self.sidebar_buttons.append(btn)
        self.queue_frame = tk.Frame(self.sidebar, bg=self.theme['sidebar'])
        self.queue_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=12)
        self.queue_label = tk.Label(self.queue_frame, text='●  就绪', bg=self.theme['sidebar'], fg=self.theme['success'], font=('Microsoft YaHei', 8))
        self.queue_label.pack(anchor='w')
        self.progress = ttk.Progressbar(self.queue_frame, mode='indeterminate', length=160)
        self.cancel_btn = tk.Label(self.queue_frame, text='停止任务', bg=self.theme['error'], fg='#ffffff', font=('Microsoft YaHei', 8, 'bold'), padx=8, pady=4, cursor='hand2')
        self.cancel_btn.bind('<Enter>', lambda e: self.cancel_btn.configure(bg=self.theme['warning']))
        self.cancel_btn.bind('<Leave>', lambda e: self.cancel_btn.configure(bg=self.theme['error']))
        self.cancel_btn.bind('<Button-1>', lambda e: self.cancel_queue())

    def build_content_area(self):
        self.right = tk.Frame(self.main_frame, bg=self.theme['bg'])
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.content_header = tk.Frame(self.right, bg=self.theme['panel'], height=54, highlightbackground=self.theme['panel_border'], highlightthickness=1)
        self.content_header.pack(side=tk.TOP, fill=tk.X)
        self.content_header.pack_propagate(False)
        self.content_title = tk.Label(self.content_header, text='工作台', bg=self.theme['panel'], fg=self.theme['fg'], font=('Microsoft YaHei', 13, 'bold'))
        self.content_title.pack(side=tk.LEFT, padx=(20, 10))
        self.content_subtitle = tk.Label(self.content_header, text='系统状态', bg=self.theme['panel'], fg=self.theme['muted'], font=('Microsoft YaHei', 8))
        self.content_subtitle.pack(side=tk.LEFT)
        self.scroll_container, self.content_canvas, self.content_frame = self.create_scrollable(self.right)
        self.scroll_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def create_scrollable(self, parent):
        outer = tk.Frame(parent, bg=self.theme['bg'])
        canvas = tk.Canvas(outer, bg=self.theme['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        inner = tk.Frame(canvas, bg=self.theme['bg'])
        window = canvas.create_window((0, 0), window=inner, anchor='nw')
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        inner.bind('<Configure>', on_configure)
        canvas.bind('<Configure>', self._on_canvas_resize)
        # 鼠标进入内容区时接管滚轮（Windows/macOS 用 MouseWheel，Linux 用 Button-4/5）
        def _on_wheel(event):
            if getattr(event, 'num', None) == 4:
                canvas.yview_scroll(-3, 'units')
            elif getattr(event, 'num', None) == 5:
                canvas.yview_scroll(3, 'units')
            elif getattr(event, 'delta', 0):
                canvas.yview_scroll(-3 if event.delta > 0 else 3, 'units')
        def _enter(e):
            self.root.bind_all('<MouseWheel>', _on_wheel)
            self.root.bind_all('<Button-4>', _on_wheel)
            self.root.bind_all('<Button-5>', _on_wheel)
        def _leave(e):
            self.root.unbind_all('<MouseWheel>')
            self.root.unbind_all('<Button-4>')
            self.root.unbind_all('<Button-5>')
        outer.bind('<Enter>', _enter)
        outer.bind('<Leave>', _leave)
        self._scroll_canvas = canvas
        self._scroll_window = window
        return outer, canvas, inner

    def _on_canvas_resize(self, event):
        self.content_canvas.itemconfig(self._scroll_window, width=event.width)
        if not getattr(self, '_last_card_tasks', None):
            return
        if not (self.current_view.startswith('category:') or self.current_view in ('favorites', 'search')):
            return
        cols = self._calc_cols(event.width)
        if cols != self._card_cols:
            if self._resize_job:
                self.root.after_cancel(self._resize_job)
            self._resize_job = self.root.after(200, self._reflow_cards)

    def _calc_cols(self, width):
        if width < 100:
            return 3
        return max(2, min(4, width // 245))

    def _reflow_cards(self):
        tasks = getattr(self, '_last_card_tasks', None)
        if not tasks:
            return
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.current_cards.clear()
        self._fill_cards(tasks)

    def build_log_panel(self):
        self.log_panel = tk.Frame(self.right, bg=self.theme['panel'], height=38, highlightbackground=self.theme['panel_border'], highlightthickness=1)
        self.log_panel.pack(side=tk.BOTTOM, fill=tk.X)
        self.log_panel.pack_propagate(False)
        self.log_header = tk.Frame(self.log_panel, bg=self.theme['panel'], height=36)
        self.log_header.pack(side=tk.TOP, fill=tk.X)
        self.log_header.pack_propagate(False)
        self.log_title = tk.Label(self.log_header, text='运行日志', bg=self.theme['panel'], fg=self.theme['fg'], font=('Microsoft YaHei', 9, 'bold'))
        self.log_title.pack(side=tk.LEFT, padx=(14, 8))
        self.log_toggle = tk.Label(self.log_header, text='展开 ▴', bg=self.theme['panel'], fg=self.theme['muted'], font=('Microsoft YaHei', 8), cursor='hand2')
        self.log_toggle.pack(side=tk.LEFT)
        self.log_toggle.bind('<Button-1>', lambda e: self.toggle_log_panel())
        self.log_collapsed = True
        self.log_action_labels = []
        clear_btn = tk.Label(self.log_header, text='清空', bg=self.theme['panel'], fg=self.theme['muted'], font=('Microsoft YaHei', 8), cursor='hand2')
        clear_btn.pack(side=tk.RIGHT, padx=4)
        clear_btn.bind('<Enter>', lambda e: clear_btn.configure(fg=self.theme['error']))
        clear_btn.bind('<Leave>', lambda e: clear_btn.configure(fg=self.theme['muted']))
        clear_btn.bind('<Button-1>', lambda e: self.clear_log())
        copy_btn = tk.Label(self.log_header, text='复制', bg=self.theme['panel'], fg=self.theme['muted'], font=('Microsoft YaHei', 8), cursor='hand2')
        copy_btn.pack(side=tk.RIGHT, padx=4)
        copy_btn.bind('<Enter>', lambda e: copy_btn.configure(fg=self.theme['accent']))
        copy_btn.bind('<Leave>', lambda e: copy_btn.configure(fg=self.theme['muted']))
        copy_btn.bind('<Button-1>', lambda e: self.copy_log())
        export_btn = tk.Label(self.log_header, text='导出', bg=self.theme['panel'], fg=self.theme['muted'], font=('Microsoft YaHei', 8), cursor='hand2')
        export_btn.pack(side=tk.RIGHT, padx=(4, 14))
        export_btn.bind('<Enter>', lambda e: export_btn.configure(fg=self.theme['accent']))
        export_btn.bind('<Leave>', lambda e: export_btn.configure(fg=self.theme['muted']))
        export_btn.bind('<Button-1>', lambda e: self.export_log())
        self.log_action_labels.extend((clear_btn, copy_btn, export_btn))
        self.log_text = scrolledtext.ScrolledText(self.log_panel, bg=self.theme['log_bg'], fg=self.theme['log_fg'], font=('Cascadia Mono', 9), state='disabled', wrap='word', relief=tk.FLAT, padx=10, pady=8, bd=0)
        for tag in ('title', 'info', 'warning', 'error', 'success', 'muted'):
            self.log_text.tag_config(tag, foreground=self.theme.get(tag, self.theme['fg']), font=('Cascadia Mono', 9))

    def on_sidebar_click(self, category):
        self.set_active_sidebar(category)
        self.search_var.set('')
        if category == 'dashboard':
            self.show_dashboard()
        elif category == 'diagnose':
            self.show_diagnose()
        else:
            self.show_category(category)

    def set_active_sidebar(self, category):
        for btn in self.sidebar_buttons:
            btn.set_active(btn.category == category)

    def clear_content(self):
        if self._refresh_stats_job:
            self.root.after_cancel(self._refresh_stats_job)
            self._refresh_stats_job = None
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.current_cards.clear()
        self.stat_cards.clear()
        self.stat_bars.clear()

    def show_dashboard(self):
        self.current_view = 'dashboard'
        self.clear_content()
        self.content_title.configure(text='工作台')
        self.content_subtitle.configure(text='系统状态与快捷操作')
        banner = GradientBanner(
            self.content_frame,
            height=112,
            start=self.theme['accent'],
            end=self.theme['banner_end'],
            icon='⚙',
            title='Windows 运维工具箱',
            subtitle='{} 个工具  ·  {} 个分类  ·  {}'.format(len(self.functions), max(0, len(self.categories) - 3), APP_VERSION),
        )
        banner.pack(fill=tk.X, padx=18, pady=(18, 10))
        self._make_dashboard_search()
        self._show_category_shortcuts()

        self._section_header('设备状态', '每 5 秒刷新')
        self.stat_cards = {}
        self.stat_bars = {}
        stats_frame = tk.Frame(self.content_frame, bg=self.theme['bg'])
        stats_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
        self.stat_cards['cpu'] = self._make_stat_card(stats_frame, 'cpu', 'CPU')
        self.stat_cards['memory'] = self._make_stat_card(stats_frame, 'memory', '内存')
        self.stat_cards['disk'] = self._make_stat_card(stats_frame, 'disk', 'C盘' if IS_WINDOWS else '磁盘')
        self.stat_cards['uptime'] = self._make_stat_card(stats_frame, 'uptime', '运行时长')
        self.stat_cards['internet'] = self._make_stat_card(stats_frame, 'internet', '网络')
        self._start_dashboard_refresh()
        self._request_stats_refresh()

        self._section_header('快捷操作', '常用任务')
        actions_frame = tk.Frame(self.content_frame, bg=self.theme['bg'])
        actions_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
        self._make_quick_button(actions_frame, '智能检测', lambda: self.on_sidebar_click('diagnose'), self.theme['error'], self.theme['card_hover'])
        if IS_WINDOWS:
            self._make_quick_button(actions_frame, '一键修复', self.one_click_repair, self.theme['success'], self.theme['card_hover'])
        self._make_quick_button(actions_frame, '全面清理', lambda: self._queue_by_id('full_cleanup'), self.theme['warning'], self.theme['card_hover'])
        self._make_quick_button(actions_frame, '网络重置', lambda: self._queue_by_id('reset_network_full'), self.theme['info'], self.theme['card_hover'])
        self._make_quick_button(actions_frame, '系统信息', lambda: self._queue_by_id('get_system_full_info'), self.theme['accent'], self.theme['card_hover'])
        self._show_dashboard_section('收藏', self.config.get('favorites', []))
        self._show_dashboard_section('最近使用', self.config.get('recent', []))

    def _make_dashboard_search(self):
        panel = tk.Frame(self.content_frame, bg=self.theme['card_border'], height=42)
        panel.pack(fill=tk.X, padx=18, pady=(0, 10))
        panel.pack_propagate(False)
        inner = tk.Frame(panel, bg=self.theme['card'])
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        tk.Label(inner, text='⌕', bg=self.theme['card'], fg=self.theme['accent'], font=('Segoe UI Symbol', 15)).pack(side=tk.LEFT, padx=(12, 7))
        tk.Label(inner, text='搜索工具', bg=self.theme['card'], fg=self.theme['muted'], font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=(0, 10))
        tk.Frame(inner, width=1, bg=self.theme['card_border']).pack(side=tk.LEFT, fill=tk.Y, pady=8)
        self.dashboard_search_entry = tk.Entry(inner, textvariable=self.search_var, bg=self.theme['card'], fg=self.theme['fg'], insertbackground=self.theme['accent'], relief=tk.FLAT, bd=0, font=('Microsoft YaHei', 10))
        self.dashboard_search_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=5)

    def _show_category_shortcuts(self):
        wrapper = tk.Frame(self.content_frame, bg=self.theme['bg'])
        wrapper.pack(fill=tk.X, padx=12, pady=(0, 8))
        categories = self.categories[3:]
        for category, label, icon in categories:
            button = tk.Label(
                wrapper,
                text='{}  {}'.format(icon, label),
                bg=self.theme['panel'],
                fg=self.theme['muted'],
                highlightbackground=self.theme['panel_border'],
                highlightthickness=1,
                font=('Microsoft YaHei', 8),
                padx=9,
                pady=7,
                cursor='hand2',
            )
            button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            button.bind('<Enter>', lambda event, item=button: item.configure(bg=self.theme['card_hover'], fg=self.theme['fg'], highlightbackground=self.theme['accent']))
            button.bind('<Leave>', lambda event, item=button: item.configure(bg=self.theme['panel'], fg=self.theme['muted'], highlightbackground=self.theme['panel_border']))
            button.bind('<Button-1>', lambda event, key=category: self.on_sidebar_click(key))

    def _section_header(self, title, meta=''):
        header = tk.Frame(self.content_frame, bg=self.theme['bg'], height=34)
        header.pack(fill=tk.X, padx=18, pady=(6, 2))
        header.pack_propagate(False)
        tk.Frame(header, width=3, bg=self.theme['accent']).pack(side=tk.LEFT, fill=tk.Y, pady=9)
        tk.Label(header, text=title, bg=self.theme['bg'], fg=self.theme['fg'], font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT, padx=(8, 8))
        if meta:
            tk.Label(header, text=meta, bg=self.theme['bg'], fg=self.theme['muted'], font=('Microsoft YaHei', 8)).pack(side=tk.LEFT)

    def _make_stat_card(self, parent, key, label):
        card = tk.Frame(parent, bg=self.theme['panel'], highlightbackground=self.theme['panel_border'], highlightthickness=1, width=150, height=84)
        card.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=6)
        card.pack_propagate(False)
        value_lbl = tk.Label(card, text='--', bg=self.theme['panel'], fg=self.theme['muted'], font=('Microsoft YaHei', 15, 'bold'))
        value_lbl.pack(pady=(10, 0))
        tk.Label(card, text=label, bg=self.theme['panel'], fg=self.theme['muted'], font=('Microsoft YaHei', 8)).pack()
        bar = tk.Canvas(card, height=4, highlightthickness=0, bd=0, bg=self.theme['sidebar_active'])
        bar.pack(fill=tk.X, padx=12, pady=(7, 9))
        self.stat_bars[key] = bar
        return value_lbl

    def _draw_stat_bar(self, key, pct, color):
        bar = self.stat_bars.get(key)
        if not bar:
            return
        try:
            bar.delete('fill')
            w = bar.winfo_width()
            if w <= 1:
                return
            frac = max(0.0, min(1.0, (pct or 0) / 100.0))
            if frac > 0:
                bar.create_rectangle(0, 0, int(w * frac), 4, fill=color, outline='', tags='fill')
        except tk.TclError:
            pass

    def _pct_color(self, value):
        if value is None:
            return self.theme['muted']
        if value < 60:
            return self.theme['success']
        if value < 85:
            return self.theme['warning']
        return self.theme['error']

    def get_system_stats(self):
        stats = {}
        stats['cpu'] = utils.get_cpu_usage()
        total, used, pct = utils.get_memory_usage()
        stats['memory'] = pct
        stats['memory_total'] = total
        stats['memory_used'] = used
        disk_data = utils.get_disk_usage()
        stats['disk'] = None
        for drive, size, used, free, pct in disk_data:
            if drive == 'C:' or drive == '/':
                stats['disk'] = pct
                stats['disk_total'] = size
                stats['disk_used'] = used
                stats['disk_free'] = free
                break
        stats['uptime'] = utils.get_uptime_seconds()
        stats['internet'] = utils.check_internet()
        return stats

    def _start_dashboard_refresh(self):
        self._refresh_stats_job = self.root.after(5000, self._refresh_dashboard_stats)

    def _refresh_dashboard_stats(self):
        if self.current_view != 'dashboard':
            return
        self._request_stats_refresh()
        self._refresh_stats_job = self.root.after(5000, self._refresh_dashboard_stats)

    def _request_stats_refresh(self):
        """后台线程采集系统指标，避免 wmic/ping 阻塞 UI（卡顿修复）"""
        if self.current_view != 'dashboard':
            return
        if getattr(self, '_stats_fetching', False):
            return
        self._stats_fetching = True

        def worker():
            try:
                stats = self.get_system_stats()
            except Exception:
                stats = {}
            self._safe_after(0, lambda s=stats: self._apply_stats(s))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_stats(self, stats):
        self._stats_fetching = False
        if self.current_view != 'dashboard' or not self.stat_cards:
            return
        try:
            for key in ('cpu', 'memory', 'disk'):
                if key not in self.stat_cards:
                    continue
                pct = stats.get(key)
                text = '未知' if pct is None else '{:.0f}%'.format(pct)
                self.stat_cards[key].configure(text=text, fg=self._pct_color(pct))
                self._draw_stat_bar(key, pct or 0, self._pct_color(pct))
            if 'uptime' in self.stat_cards:
                up = stats.get('uptime')
                self.stat_cards['uptime'].configure(text=utils.format_seconds(up) if up else '未知', fg=self.theme['warning'])
            if 'internet' in self.stat_cards:
                online = stats.get('internet')
                self.stat_cards['internet'].configure(text='在线' if online else '离线', fg=self.theme['success'] if online else self.theme['error'])
        except tk.TclError:
            pass

    def _make_quick_button(self, parent, text, command, color, hover_color):
        btn = tk.Label(parent, text='›  ' + text, bg=self.theme['panel'], fg=color, highlightbackground=self.theme['panel_border'], highlightthickness=1, font=('Microsoft YaHei', 9, 'bold'), padx=14, pady=9, cursor='hand2')
        btn.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=6)
        btn.bind('<Enter>', lambda e: btn.configure(bg=hover_color, highlightbackground=color))
        btn.bind('<Leave>', lambda e: btn.configure(bg=self.theme['panel'], highlightbackground=self.theme['panel_border']))
        btn.bind('<Button-1>', lambda e: command())

    def _queue_by_id(self, task_id):
        task = self.get_task_by_id(task_id)
        if task:
            self.run_function(task)

    def _show_dashboard_section(self, title, ids):
        self._section_header(title, '{} 项'.format(len(ids)))
        section = tk.Frame(self.content_frame, bg=self.theme['panel'], highlightbackground=self.theme['panel_border'], highlightthickness=1)
        section.pack(fill=tk.X, padx=18, pady=(0, 7))
        if not ids:
            tk.Label(section, text='暂无内容', bg=self.theme['panel'], fg=self.theme['muted'], font=('Microsoft YaHei', 8)).pack(pady=12)
            return
        row = tk.Frame(section, bg=self.theme['panel'])
        row.pack(fill=tk.X, padx=6, pady=6)
        for i, fid in enumerate(ids[:6]):
            task = self.get_task_by_id(fid)
            if not task:
                continue
            if i > 0 and i % 3 == 0:
                row = tk.Frame(section, bg=self.theme['panel'])
                row.pack(fill=tk.X, padx=6, pady=(0, 6))
            btn = tk.Label(row, text='{}  {}'.format(task['icon'], task['name']), bg=self.theme['card'], fg=self.theme['fg'], highlightbackground=self.theme['card_border'], highlightthickness=1, font=('Microsoft YaHei', 8), padx=10, pady=6, cursor='hand2')
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=self.theme['card_hover'], highlightbackground=self.theme['accent']))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=self.theme['card']))
            btn.bind('<Button-1>', lambda e, t=task: self.run_function(t))

    # ==================== 智能诊断 ====================

    def _mk_btn(self, parent, text, bg, hover, command, fg='#ffffff'):
        """创建带悬停效果、可禁用的按钮"""
        btn = tk.Label(parent, text=text, bg=bg, fg=fg, font=('Microsoft YaHei', 9, 'bold'), padx=14, pady=6, cursor='hand2')
        btn._enabled = True
        btn._base_bg = bg
        btn.bind('<Enter>', lambda e: btn.configure(bg=hover) if btn._enabled else None)
        btn.bind('<Leave>', lambda e: btn.configure(bg=bg) if btn._enabled else None)
        btn.bind('<Button-1>', lambda e: command() if btn._enabled else None)
        return btn

    def _set_btn_enabled(self, btn, enabled):
        btn._enabled = enabled
        if enabled:
            btn.configure(bg=btn._base_bg, cursor='hand2')
        else:
            btn.configure(bg=self.theme['muted'], cursor='arrow')

    def show_diagnose(self):
        self.current_view = 'diagnose'
        self.clear_content()
        self.content_title.configure(text='智能诊断')
        self.content_subtitle.configure(text='一键检测修复 · 向导式排查')
        wizard_banner = GradientBanner(self.content_frame, height=92, start=self.theme['error'], end=self.theme['info'],
                                       icon='🩺', title='不知道哪里出了问题？点我试试看',
                                       subtitle='回答几个小问题，帮你定位故障并给出针对性修复方案')
        wizard_banner.pack(fill=tk.X, padx=20, pady=(20, 10))
        wizard_banner.configure(cursor='hand2')
        wizard_banner.bind('<Button-1>', lambda e: self.show_wizard('root', reset=True))
        card = tk.Frame(self.content_frame, bg=self.theme['card'], highlightbackground=self.theme['card_border'], highlightthickness=1)
        card.pack(fill=tk.X, padx=20, pady=10)
        inner = tk.Frame(card, bg=self.theme['card'])
        inner.pack(fill=tk.X, padx=16, pady=14)
        tk.Label(inner, text='⚡ 一键检测并修复', bg=self.theme['card'], fg=self.theme['fg'], font=('Microsoft YaHei', 12, 'bold')).pack(anchor='w')
        tk.Label(inner, text='自动检查互联网连接、DNS 解析、默认网关、磁盘空间、内存占用、系统错误等共 {} 项指标。检测过程只读不改系统，发现问题可直接修复。'.format(len(diagnose.get_checks())),
                 bg=self.theme['card'], fg=self.theme['muted'], font=('Microsoft YaHei', 9), wraplength=780, justify=tk.LEFT).pack(anchor='w', pady=(6, 10))
        btn_row = tk.Frame(inner, bg=self.theme['card'])
        btn_row.pack(fill=tk.X)
        self.detect_btn = self._mk_btn(btn_row, '开始检测', self.theme['accent'], self.theme['accent_hover'], self.start_detection)
        self.detect_btn.pack(side=tk.LEFT)
        self.fix_all_btn = self._mk_btn(btn_row, '一键修复发现的问题', self.theme['success'], '#16a34a', self.fix_all_detected)
        self.fix_all_btn.pack(side=tk.LEFT, padx=(10, 0))
        self._set_btn_enabled(self.fix_all_btn, False)
        self.detect_results = tk.Frame(self.content_frame, bg=self.theme['bg'])
        self.detect_results.pack(fill=tk.X, padx=20, pady=(0, 10))
        self.detected_fix_ids = []

    def start_detection(self):
        if getattr(self, '_detecting', False):
            return
        self._detecting = True
        self.detected_fix_ids = []
        self._set_btn_enabled(self.fix_all_btn, False)
        for w in self.detect_results.winfo_children():
            w.destroy()
        self.detect_btn.configure(text='正在检测…')
        self._set_btn_enabled(self.detect_btn, False)
        self.log('开始智能检测（{} 项）...'.format(len(diagnose.get_checks())), 'info')
        threading.Thread(target=self._detection_worker, daemon=True).start()

    def _detection_worker(self):
        for chk in diagnose.get_checks():
            try:
                res = chk['run']()
            except Exception as e:
                res = {'status': 'warn', 'message': '检测未完成: {}'.format(e), 'fixes': []}
            self._safe_after(0, lambda c=chk, r=res: self._append_check_result(c, r))
        self._safe_after(0, self._detection_done)

    def _append_check_result(self, chk, res):
        if not self.detect_results.winfo_exists():
            return
        colors = {'ok': self.theme['success'], 'warn': self.theme['warning'], 'error': self.theme['error']}
        icons = {'ok': '✅', 'warn': '⚠️', 'error': '❌'}
        color = colors.get(res['status'], self.theme['muted'])
        row = tk.Frame(self.detect_results, bg=self.theme['card'], highlightbackground=self.theme['card_border'], highlightthickness=1)
        row.pack(fill=tk.X, pady=4)
        inner = tk.Frame(row, bg=self.theme['card'])
        inner.pack(fill=tk.X, padx=12, pady=8)
        left = tk.Frame(inner, bg=self.theme['card'])
        left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(left, text='{} {} {}'.format(icons.get(res['status'], '❔'), chk['icon'], chk['name']),
                 bg=self.theme['card'], fg=color, font=('Microsoft YaHei', 10, 'bold')).pack(anchor='w')
        tk.Label(left, text=res['message'], bg=self.theme['card'], fg=self.theme['muted'],
                 font=('Microsoft YaHei', 9), wraplength=560, justify=tk.LEFT).pack(anchor='w')
        if res['fixes']:
            for fid in res['fixes']:
                if fid not in self.detected_fix_ids:
                    self.detected_fix_ids.append(fid)
            btn_area = tk.Frame(inner, bg=self.theme['card'])
            btn_area.pack(side=tk.RIGHT, padx=(10, 0))
            for fid in res['fixes'][:3]:
                task = self.get_task_by_id(fid)
                if not task:
                    continue
                b = self._mk_btn(btn_area, task['name'], self.theme['sidebar_active'], self.theme['sidebar_hover'],
                                 lambda t=task: self.run_function(t), fg=self.theme['fg'])
                b.pack(side=tk.LEFT, padx=3)
            if len(res['fixes']) > 3:
                tk.Label(btn_area, text='等{}项'.format(len(res['fixes'])), bg=self.theme['card'],
                         fg=self.theme['muted'], font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=4)

    def _detection_done(self):
        self._detecting = False
        if not self.detect_results.winfo_exists():
            return
        self.detect_btn.configure(text='重新检测')
        self._set_btn_enabled(self.detect_btn, True)
        summary = tk.Frame(self.detect_results, bg=self.theme['bg'])
        summary.pack(fill=tk.X, pady=(8, 0))
        if self.detected_fix_ids:
            self._set_btn_enabled(self.fix_all_btn, True)
            tk.Label(summary, text='检测完成：发现可修复的问题，建议点击「一键修复发现的问题」，或逐项手动修复。',
                     bg=self.theme['bg'], fg=self.theme['warning'], font=('Microsoft YaHei', 9, 'bold')).pack(anchor='w')
            self.log('智能检测完成，发现 {} 项建议修复'.format(len(self.detected_fix_ids)), 'warning')
        else:
            tk.Label(summary, text='🎉 检测完成：各项指标正常，电脑状态良好！',
                     bg=self.theme['bg'], fg=self.theme['success'], font=('Microsoft YaHei', 10, 'bold')).pack(anchor='w')
            self.log('智能检测完成，未发现问题', 'success')

    def fix_all_detected(self):
        self.queue_fix_list(self.detected_fix_ids, '一键修复')

    def queue_fix_list(self, ids, title='批量修复'):
        """按顺序批量执行一组修复工具（统一确认一次，危险操作前自动建还原点）"""
        tasks = [self.get_task_by_id(i) for i in ids]
        tasks = [t for t in tasks if t]
        if not tasks:
            return
        if any(t.get('admin') for t in tasks) and not self.is_admin:
            self.log('{} 需要管理员权限，请先提升权限'.format(title), 'warning')
            if messagebox.askyesno('需要管理员权限', '部分操作需要管理员权限，是否立即提升？'):
                self.elevate_privilege()
            return
        has_danger = any(t.get('danger') for t in tasks)
        names = '、'.join(t['name'] for t in tasks[:6])
        if len(tasks) > 6:
            names += ' 等 {} 项'.format(len(tasks))
        msg = '将依次执行 {} 项操作：\n{}'.format(len(tasks), names)
        if has_danger:
            msg += '\n\n其中包含危险操作'
            msg += '，将先自动创建系统还原点。' if self.config.get('auto_backup', True) else '。'
        if not messagebox.askyesno(title, msg + '\n\n是否继续？'):
            return
        if has_danger and self.config.get('auto_backup', True):
            self.log('自动备份：正在创建系统还原点...', 'info')
            rp = self.get_task_by_id('create_restore_point')
            if rp:
                self.queue.append(rp)
        for t in tasks:
            if t['id'] == 'create_restore_point':
                continue
            self.queue.append(t)
            self.add_recent(t['id'])
        self._process_queue()

    # ==================== 诊断向导 ====================

    def show_wizard(self, node_id, reset=False):
        self.current_view = 'wizard'
        self.wizard_node = node_id
        if reset:
            self.wizard_history = []
        self.clear_content()
        self.content_title.configure(text='智能诊断向导')
        self.content_subtitle.configure(text='不知道哪里出了问题？点我试试看')
        node = self.wizard_tree[node_id]
        bar = tk.Frame(self.content_frame, bg=self.theme['bg'])
        bar.pack(fill=tk.X, padx=20, pady=(16, 4))
        back_home = tk.Label(bar, text='‹ 返回智能诊断', bg=self.theme['bg'], fg=self.theme['accent'], font=('Microsoft YaHei', 9, 'bold'), cursor='hand2')
        back_home.pack(side=tk.LEFT)
        back_home.bind('<Button-1>', lambda e: self.show_diagnose())
        if self.wizard_history:
            back_step = tk.Label(bar, text='‹ 上一步', bg=self.theme['bg'], fg=self.theme['muted'], font=('Microsoft YaHei', 9), cursor='hand2')
            back_step.pack(side=tk.LEFT, padx=(16, 0))
            back_step.bind('<Button-1>', self.wizard_back)
        restart = tk.Label(bar, text='重新诊断', bg=self.theme['bg'], fg=self.theme['muted'], font=('Microsoft YaHei', 9), cursor='hand2')
        restart.pack(side=tk.RIGHT)
        restart.bind('<Button-1>', lambda e: self.show_wizard('root', reset=True))
        if node.get('leaf'):
            self._render_wizard_leaf(node)
        else:
            self._render_wizard_question(node_id, node)

    def wizard_back(self, e=None):
        if self.wizard_history:
            self.show_wizard(self.wizard_history.pop())

    def _render_wizard_question(self, node_id, node):
        card = tk.Frame(self.content_frame, bg=self.theme['card'], highlightbackground=self.theme['card_border'], highlightthickness=1)
        card.pack(fill=tk.X, padx=20, pady=10)
        inner = tk.Frame(card, bg=self.theme['card'])
        inner.pack(fill=tk.X, padx=20, pady=18)
        tk.Label(inner, text='❓ ' + node['q'], bg=self.theme['card'], fg=self.theme['fg'],
                 font=('Microsoft YaHei', 14, 'bold'), wraplength=780, justify=tk.LEFT).pack(anchor='w')
        if node.get('desc'):
            tk.Label(inner, text=node['desc'], bg=self.theme['card'], fg=self.theme['muted'],
                     font=('Microsoft YaHei', 9), wraplength=780, justify=tk.LEFT).pack(anchor='w', pady=(4, 0))
        for opt in node['options']:
            self._render_wizard_option(node_id, opt)

    def _render_wizard_option(self, node_id, opt):
        row = tk.Frame(self.content_frame, bg=self.theme['card'], highlightbackground=self.theme['card_border'], highlightthickness=1, cursor='hand2')
        row.pack(fill=tk.X, padx=20, pady=4)
        inner = tk.Frame(row, bg=self.theme['card'])
        inner.pack(fill=tk.X, padx=14, pady=12)
        icon_lbl = tk.Label(inner, text=opt['icon'], bg=self.theme['card'], fg=self.theme['fg'], font=('Segoe UI Emoji', 16))
        icon_lbl.pack(side=tk.LEFT)
        text_lbl = tk.Label(inner, text=opt['label'], bg=self.theme['card'], fg=self.theme['fg'], font=('Microsoft YaHei', 11))
        text_lbl.pack(side=tk.LEFT, padx=(10, 0))
        arrow_lbl = tk.Label(inner, text='›', bg=self.theme['card'], fg=self.theme['muted'], font=('Microsoft YaHei', 16))
        arrow_lbl.pack(side=tk.RIGHT)
        widgets = [row, inner, icon_lbl, text_lbl, arrow_lbl]

        def on_click(e=None):
            if opt.get('action') == 'detect':
                self.show_diagnose()
                self.start_detection()
            else:
                self.wizard_history.append(node_id)
                self.show_wizard(opt['next'])

        def on_enter(e=None):
            hover = self.theme.get('card_hover', self.theme['card'])
            row.configure(bg=hover, highlightbackground=self.theme['accent'])
            for w in widgets[1:]:
                w.configure(bg=hover)

        def on_leave(e=None):
            row.configure(bg=self.theme['card'], highlightbackground=self.theme['card_border'])
            for w in widgets[1:]:
                w.configure(bg=self.theme['card'])

        for w in widgets:
            w.bind('<Button-1>', on_click)
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)

    def _render_wizard_leaf(self, node):
        card = tk.Frame(self.content_frame, bg=self.theme['card'], highlightbackground=self.theme['card_border'], highlightthickness=1)
        card.pack(fill=tk.X, padx=20, pady=10)
        inner = tk.Frame(card, bg=self.theme['card'])
        inner.pack(fill=tk.X, padx=20, pady=18)
        tk.Label(inner, text='🎯 ' + node['title'], bg=self.theme['card'], fg=self.theme['fg'],
                 font=('Microsoft YaHei', 13, 'bold'), wraplength=780, justify=tk.LEFT).pack(anchor='w')
        tk.Label(inner, text=node['desc'], bg=self.theme['card'], fg=self.theme['muted'],
                 font=('Microsoft YaHei', 10), wraplength=780, justify=tk.LEFT).pack(anchor='w', pady=(6, 0))
        if node.get('fixes'):
            tk.Label(inner, text='建议操作', bg=self.theme['card'], fg=self.theme['fg'],
                     font=('Microsoft YaHei', 10, 'bold')).pack(anchor='w', pady=(14, 6))
            for fid, reason in node['fixes']:
                task = self.get_task_by_id(fid)
                if not task:
                    continue
                frow = tk.Frame(inner, bg=self.theme['bg'], highlightbackground=self.theme['card_border'], highlightthickness=1)
                frow.pack(fill=tk.X, pady=3)
                finner = tk.Frame(frow, bg=self.theme['bg'])
                finner.pack(fill=tk.X, padx=10, pady=8)
                tk.Label(finner, text='{} {}'.format(task['icon'], task['name']), bg=self.theme['bg'],
                         fg=self.theme['fg'], font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT)
                tk.Label(finner, text=reason, bg=self.theme['bg'], fg=self.theme['muted'],
                         font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=(10, 0))
                run_btn = self._mk_btn(finner, '运行', self.theme['accent'], self.theme['accent_hover'],
                                       lambda t=task: self.run_function(t))
                run_btn.pack(side=tk.RIGHT)
            if len(node['fixes']) > 1:
                all_btn = self._mk_btn(inner, '全部按顺序执行', self.theme['success'], '#16a34a',
                                       lambda: self.queue_fix_list([f[0] for f in node['fixes']], '向导修复'))
                all_btn.pack(anchor='w', pady=(10, 0))
        if node.get('tips'):
            tk.Label(inner, text='温馨提示', bg=self.theme['card'], fg=self.theme['fg'],
                     font=('Microsoft YaHei', 10, 'bold')).pack(anchor='w', pady=(16, 6))
            for tip in node['tips']:
                tk.Label(inner, text='💡 ' + tip, bg=self.theme['card'], fg=self.theme['muted'],
                         font=('Microsoft YaHei', 9), wraplength=780, justify=tk.LEFT).pack(anchor='w', pady=1)
        bottom = tk.Frame(inner, bg=self.theme['card'])
        bottom.pack(fill=tk.X, pady=(18, 0))
        again = self._mk_btn(bottom, '问题没解决？换个方向重新诊断', self.theme['sidebar_active'], self.theme['sidebar_hover'],
                             lambda: self.show_wizard('root', reset=True), fg=self.theme['fg'])
        again.pack(side=tk.LEFT)

    def show_category(self, category):
        if category == 'favorites':
            self.current_view = 'favorites'
        else:
            self.current_view = 'category:' + category
        self.clear_content()
        if category == 'favorites':
            tasks = [t for t in self.functions if t['id'] in self.config.get('favorites', [])]
            title = '我的收藏'
            subtitle = '共 {} 个收藏工具'.format(len(tasks))
        else:
            tasks = [t for t in self.functions if t['category'] == category]
            title = self._category_label(category)
            subtitle = '共 {} 个工具'.format(len(tasks))
        self.content_title.configure(text=title)
        self.content_subtitle.configure(text=subtitle)
        if not tasks:
            self._show_empty('该分类下暂无内容')
            return
        self._fill_cards(tasks)

    def _category_label(self, category):
        for cat_id, label, icon in self.categories:
            if cat_id == category:
                return icon + ' ' + label
        return category

    def _fill_cards(self, tasks):
        self._last_card_tasks = tasks
        width = self.content_canvas.winfo_width()
        cols = self._calc_cols(width)
        self._card_cols = cols
        wrap = max(200, (width // cols) - 110) if width > 200 else 320
        row = None
        for i, task in enumerate(tasks):
            if i % cols == 0:
                row = tk.Frame(self.content_frame, bg=self.theme['bg'])
                row.pack(fill=tk.X, padx=20, pady=(0, 12))
                for c in range(cols):
                    row.columnconfigure(c, weight=1, uniform='cardcol')
            card = ActionCard(row, task, self, self.theme, wrap=wrap)
            card.grid(row=0, column=i % cols, padx=8, pady=8, sticky='new')
            self.current_cards.append(card)
        self.content_canvas.update_idletasks()
        self.content_canvas.configure(scrollregion=self.content_canvas.bbox('all'))

    def _show_empty(self, text):
        tk.Label(self.content_frame, text=text, bg=self.theme['bg'], fg=self.theme['muted'], font=('Microsoft YaHei', 12)).pack(pady=60)

    def _on_search_changed(self):
        """搜索输入防抖：停止输入 250ms 后才真正搜索，避免边打字边重建界面"""
        if self._search_job:
            self.root.after_cancel(self._search_job)
        self._search_job = self.root.after(250, self.perform_search)

    def perform_search(self, *args):
        keyword = self.search_var.get().strip().lower()
        if not keyword:
            if self.current_view == 'search':
                self.set_active_sidebar('dashboard')
                self.show_dashboard()
            return
        self.current_view = 'search'
        self.clear_content()
        self.set_active_sidebar(None)
        tasks = [t for t in self.functions if keyword in t['name'].lower() or keyword in t['desc'].lower() or keyword in t['id'].lower()]
        self.content_title.configure(text='搜索结果')
        self.content_subtitle.configure(text='关键词 {} 共 {} 个结果'.format(keyword, len(tasks)))
        if not tasks:
            self._show_empty('未找到匹配的工具')
            return
        self._fill_cards(tasks)

    def run_function(self, task):
        if not task or not isinstance(task, dict):
            return
        if task.get('admin') and not self.is_admin:
            self.log('{} 需要管理员权限，请先提升权限'.format(task['name']), 'warning')
            if messagebox.askyesno('需要管理员权限', '该操作需要管理员权限，是否立即提升？'):
                self.elevate_privilege()
            return
        if task.get('danger'):
            if not messagebox.askyesno('危险操作确认', '操作 {} 可能影响系统稳定性，是否继续？'.format(task['name'])):
                return
            if self.config.get('auto_backup', True):
                self.log('自动备份：正在创建系统还原点...', 'info')
                self.queue.append(self.get_task_by_id('create_restore_point'))
        self.add_recent(task['id'])
        self.queue.append(task)
        self._process_queue()

    def _process_queue(self):
        with self.queue_lock:
            if self.cancelled:
                self.queue.clear()
                self.cancelled = False
                self.running_task = None
                self.progress_stop()
                self.set_status('就绪')
                return
            if self.running_task or not self.queue:
                if not self.queue:
                    self.progress_stop()
                    self.set_status('就绪')
                return
            task = self.queue.popleft()
            self.running_task = task
        self.progress_start()
        self.set_status('正在运行: {}'.format(task['name']))
        self.task_thread = threading.Thread(target=self._task_worker, args=(task,), daemon=True)
        self.task_thread.start()

    def _task_worker(self, task):
        try:
            self.log('开始执行: {}'.format(task['name']), 'title')
            result = task['func'](log=self.log)
            if result:
                self.log('{} 执行成功'.format(task['name']), 'success')
            else:
                self.log('{} 执行完成，但可能未成功'.format(task['name']), 'warning')
        except Exception as e:
            self.log('{} 执行失败: {}'.format(task['name'], e), 'error')
        finally:
            self.running_task = None
            self._safe_after(0, self._process_queue)

    def _update_queue_label(self):
        if self.running_task:
            self.set_status('正在运行: {}'.format(self.running_task['name']))
        else:
            self.set_status('就绪')

    def cancel_queue(self, e=None):
        with self.queue_lock:
            self.queue.clear()
            self.cancelled = True
        self.log('已取消剩余任务队列', 'warning')
        self.progress_stop()
        self.set_status('已取消')

    def progress_start(self):
        if self.log_collapsed:
            self.toggle_log_panel()
        if not self.progress.winfo_manager():
            self.progress.pack(fill=tk.X, pady=(7, 0))
        if not self.cancel_btn.winfo_manager():
            self.cancel_btn.pack(fill=tk.X, pady=(7, 0))
        self.progress.configure(mode='indeterminate')
        self.progress.start(10)

    def progress_stop(self):
        self.progress.stop()
        self.progress.configure(mode='determinate', value=0)
        self.progress.pack_forget()
        self.cancel_btn.pack_forget()

    def set_status(self, text):
        idle = text == '就绪'
        self.queue_label.configure(
            text=('●  ' if idle else '◉  ') + text,
            fg=self.theme['success'] if idle else self.theme['warning'],
        )

    def show_task_detail(self, task):
        top = tk.Toplevel(self.root)
        top.title('工具详情')
        top.geometry('450x320')
        top.configure(bg=self.theme['bg'])
        top.transient(self.root)
        top.grab_set()
        x = self.root.winfo_x() + (self.root.winfo_width() - 450) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 320) // 2
        top.geometry('+{}+{}'.format(x, y))
        tk.Label(top, text='{} {}'.format(task['icon'], task['name']), bg=self.theme['bg'], fg=self.theme['fg'], font=('Microsoft YaHei', 14, 'bold')).pack(pady=(20, 10))
        tk.Label(top, text=task['desc'], bg=self.theme['bg'], fg=self.theme['muted'], font=('Microsoft YaHei', 10), wraplength=400, justify=tk.LEFT).pack(pady=10)
        tags = []
        if task.get('danger'):
            tags.append('危险操作：可能影响系统稳定性')
        if task.get('admin'):
            tags.append('需要管理员权限')
        if task.get('reboot'):
            tags.append('需要重启生效')
        if not tags:
            tags.append('安全操作')
        tk.Label(top, text=' · '.join(tags), bg=self.theme['bg'], fg=self.theme['accent'], font=('Microsoft YaHei', 9)).pack(pady=10)
        btn = tk.Label(top, text='运行', bg=self.theme['accent'], fg=self.theme['accent_fg'], font=('Microsoft YaHei', 10, 'bold'), padx=20, pady=6, cursor='hand2')
        btn.pack(pady=20)
        btn.bind('<Enter>', lambda e: btn.configure(bg=self.theme['accent_hover']))
        btn.bind('<Leave>', lambda e: btn.configure(bg=self.theme['accent']))
        btn.bind('<Button-1>', lambda e: (top.destroy(), self.run_function(task)))

    def toggle_favorite(self, task_id):
        favs = self.config.get('favorites', [])
        if task_id in favs:
            favs.remove(task_id)
            self.log('已取消收藏', 'info')
        else:
            favs.insert(0, task_id)
            self.log('已收藏该工具', 'success')
        self.config['favorites'] = favs
        self.save_config()
        for card in self.current_cards:
            card.update_star()
        if self.current_view == 'favorites':
            self.show_category('favorites')
        elif self.current_view == 'dashboard':
            self.show_dashboard()

    def add_recent(self, task_id):
        recent = self.config.get('recent', [])
        if task_id in recent:
            recent.remove(task_id)
        recent.insert(0, task_id)
        self.config['recent'] = recent[:10]
        self.save_config()
        if self.current_view == 'dashboard':
            self.show_dashboard()

    def get_task_by_id(self, task_id):
        for t in self.functions:
            if t['id'] == task_id:
                return t
        return None
    def log(self, msg, tag='info'):
        if self.root and not self._closing:
            self._safe_after(0, lambda: self._append_log(msg, tag))

    def _append_log(self, msg, tag='info'):
        ts = datetime.now().strftime('%H:%M:%S')
        self.log_text.configure(state='normal')
        for line in str(msg).splitlines():
            self.log_text.insert('end', '[{}] {}'.format(ts, line) + chr(10), tag)
        self.log_text.configure(state='disabled')
        self.log_text.see('end')

    def toggle_log_panel(self):
        """折叠/展开日志面板，给内容区更多空间"""
        self.log_collapsed = not self.log_collapsed
        if self.log_collapsed:
            self.log_text.pack_forget()
            self.log_panel.configure(height=38)
            self.log_toggle.configure(text='展开 ▴')
        else:
            self.log_panel.configure(height=220)
            self.log_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))
            self.log_toggle.configure(text='收起 ▾')

    def clear_log(self, e=None):
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.configure(state='disabled')

    def copy_log(self, e=None):
        content = self.log_text.get('1.0', tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.log('日志已复制到剪贴板', 'success')

    def export_log(self, e=None):
        path = filedialog.asksaveasfilename(defaultextension='.log', filetypes=[('日志文件', '*.log'), ('文本文件', '*.txt'), ('所有文件', '*.*')])
        if not path:
            return
        try:
            content = self.log_text.get('1.0', tk.END)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.log('日志已导出: {}'.format(path), 'success')
        except Exception as e:
            self.log('导出日志失败: {}'.format(e), 'error')

    def export_full_report(self, e=None):
        path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('文本文件', '*.txt'), ('所有文件', '*.*')])
        if not path:
            return
        def worker():
            self.log('开始导出完整系统报告...', 'info')
            lines = ['Windows 运维工具箱 - 系统完整报告', '生成时间: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '-' * 40, '']
            for task in self.functions:
                if task['category'] == 'info':
                    lines.append('[{}]'.format(task['name']))
                    try:
                        task['func'](log=lambda msg: lines.append('  ' + msg))
                    except Exception as e:
                        lines.append('  收集失败: {}'.format(e))
                    lines.append('')
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(chr(10).join(lines))
                self.log('完整报告已保存: {}'.format(path), 'success')
            except Exception as e:
                self.log('保存报告失败: {}'.format(e), 'error')
        threading.Thread(target=worker, daemon=True).start()

    def update_admin_badge(self):
        if self.is_admin:
            self.admin_badge.configure(text='● 管理员', bg=self.theme['tag_bg'], fg=self.theme['success'])
            self.elevate_btn.pack_forget()
        else:
            self.admin_badge.configure(text='● 普通用户', bg=self.theme['tag_bg'], fg=self.theme['warning'])
            self.elevate_btn.pack(side=tk.RIGHT, padx=4)

    def elevate_privilege(self, e=None):
        self.log('正在请求管理员权限...', 'info')
        if utils.run_as_admin():
            self.log('已启动管理员权限窗口，请确认', 'info')
            self.root.after(1000, self.root.quit)
        else:
            self.log('请求管理员权限失败', 'error')

    def toggle_theme(self, e=None):
        self.theme_name = 'dark' if self.theme_name == 'light' else 'light'
        self.theme = THEMES[self.theme_name]
        self.config['theme'] = self.theme_name
        self.save_config()
        self._apply_theme()

    def _apply_theme(self):
        self.root.configure(bg=self.theme['bg'])
        self.main_frame.configure(bg=self.theme['bg'])
        self.header.configure(bg=self.theme['header'], highlightbackground=self.theme['header_border'])
        self.header_logo_lbl.configure(bg=self.theme['header'], fg=self.theme['accent'])
        self.header_title_lbl.configure(bg=self.theme['header'], fg=self.theme['fg'])
        for item in self.header_nav_items:
            item.configure(bg=self.theme['header'], fg=self.theme['muted'])
        self.admin_badge.configure(
            bg=self.theme['tag_bg'],
            fg=self.theme['success'] if self.is_admin else self.theme['warning'],
        )
        self.theme_btn.configure(bg=self.theme['header'], fg=self.theme['muted'], text='☀' if self.theme_name == 'light' else '☾')
        self.elevate_btn.configure(bg=self.theme['accent'], fg=self.theme['accent_fg'])
        if self.repair_btn:
            self.repair_btn.configure(bg=self.theme['success'], fg=self.theme['accent_fg'])
        self.export_btn.configure(bg=self.theme['sidebar_active'], fg=self.theme['info'])
        self.backup_chk.configure(bg=self.theme['header'], fg=self.theme['muted'], activebackground=self.theme['header'], activeforeground=self.theme['fg'], selectcolor=self.theme['sidebar_active'])
        self.sidebar.configure(bg=self.theme['sidebar'], highlightbackground=self.theme['header_border'])
        self.sidebar_heading.configure(bg=self.theme['sidebar'])
        self.sidebar_logo_lbl.configure(bg=self.theme['sidebar'], fg=self.theme['accent'])
        self.sidebar_title_lbl.configure(bg=self.theme['sidebar'], fg=self.theme['fg'])
        self.search_frame.configure(bg=self.theme['card_border'])
        self.search_inner.configure(bg=self.theme['card'])
        self.search_icon.configure(bg=self.theme['card'], fg=self.theme['muted'])
        self.cat_frame.configure(bg=self.theme['sidebar'])
        self.queue_frame.configure(bg=self.theme['sidebar'])
        self.queue_label.configure(bg=self.theme['sidebar'], fg=self.theme['success'] if not self.running_task else self.theme['warning'])
        self.right.configure(bg=self.theme['bg'])
        for key, lbl in self.stat_cards.items():
            if key in ('cpu', 'memory', 'disk'):
                try:
                    val = float(lbl.cget('text').replace('%', ''))
                    lbl.configure(bg=self.theme['panel'], fg=self._pct_color(val))
                except Exception:
                    lbl.configure(bg=self.theme['panel'], fg=self.theme['fg'])
            else:
                lbl.configure(bg=self.theme['panel'], fg=self.theme['fg'])
        self.content_header.configure(bg=self.theme['panel'], highlightbackground=self.theme['panel_border'])
        self.content_title.configure(bg=self.theme['panel'], fg=self.theme['fg'])
        self.content_subtitle.configure(bg=self.theme['panel'], fg=self.theme['muted'])
        self.scroll_container.configure(bg=self.theme['bg'])
        self.content_canvas.configure(bg=self.theme['bg'])
        self.content_frame.configure(bg=self.theme['bg'])
        self.log_panel.configure(bg=self.theme['panel'], highlightbackground=self.theme['panel_border'])
        self.log_header.configure(bg=self.theme['panel'])
        self.log_title.configure(bg=self.theme['panel'], fg=self.theme['fg'])
        self.log_toggle.configure(bg=self.theme['panel'], fg=self.theme['muted'])
        for item in self.log_action_labels:
            item.configure(bg=self.theme['panel'], fg=self.theme['muted'])
        self.log_text.configure(bg=self.theme['log_bg'], fg=self.theme['log_fg'])
        self.search_entry.configure(bg=self.theme['card'], fg=self.theme['fg'], insertbackground=self.theme['accent'])
        for tag in ('title', 'info', 'warning', 'error', 'success', 'muted'):
            self.log_text.tag_config(tag, foreground=self.theme.get(tag, self.theme['fg']))
        self.setup_styles()
        for btn in self.sidebar_buttons:
            btn.refresh_theme(self.theme)
        self.refresh_current_view()

    def refresh_current_view(self):
        if self.current_view == 'dashboard':
            self.show_dashboard()
        elif self.current_view == 'favorites':
            self.show_category('favorites')
        elif self.current_view == 'diagnose':
            self.show_diagnose()
        elif self.current_view == 'wizard':
            self.show_wizard(getattr(self, 'wizard_node', 'root'))
        elif self.current_view.startswith('category:'):
            cat = self.current_view.split(':', 1)[1]
            self.show_category(cat)
        elif self.current_view == 'search':
            self.perform_search()

    def _on_auto_backup_toggle(self):
        self.config['auto_backup'] = self.backup_var.get()
        self.save_config()

    def one_click_repair(self, e=None):
        if not self.is_admin:
            self.log('一键修复需要管理员权限', 'warning')
            messagebox.showwarning('需要管理员权限', '一键修复会修改系统设置，请先提升权限')
            return
        ids = ['create_restore_point', 'flush_dns', 'clean_temp_files', 'sfc_scannow', 'clean_dns_cache']
        if not messagebox.askyesno('一键修复', '将依次执行 {} 项操作：创建还原点、刷新DNS、清理临时文件、SFC检查、清理DNS缓存。是否继续？'.format(len(ids))):
            return
        for tid in ids:
            task = self.get_task_by_id(tid)
            if task:
                self.queue.append(task)
        self._process_queue()

    def bind_shortcuts(self):
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus())
        self.root.bind('<Control-t>', self.toggle_theme)
        self.root.bind('<F1>', lambda e: self.on_sidebar_click('dashboard'))
        self.root.bind('<F2>', lambda e: self.on_sidebar_click('diagnose'))
        self.root.bind('<Escape>', self._on_escape)

    def _on_escape(self, e=None):
        if self.search_var.get():
            self.search_var.set('')
        else:
            self.cancel_queue()
