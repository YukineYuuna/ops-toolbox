#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Windows 运维工具箱 v3.0 启动器
'''
import os
import sys

def center_window(w, width, height):
    screen_width = w.winfo_screenwidth()
    screen_height = w.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    w.geometry('{}x{}+{}+{}'.format(width, height, x, y))

def run_tk_fallback():
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    app_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, app_dir)
    from modules.platform_detect import APP_NAME
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.configure(bg='#0b1016')
    center_window(splash, 400, 220)
    tk.Label(splash, text='⚙', bg='#0b1016', fg='#43c6ac', font=('Segoe UI Symbol', 44, 'bold')).pack(pady=(30, 10))
    tk.Label(splash, text=APP_NAME, bg='#0b1016', fg='#edf4f7', font=('Microsoft YaHei', 16, 'bold')).pack()
    tk.Label(splash, text='正在加载工作台...', bg='#0b1016', fg='#8fa0ac', font=('Microsoft YaHei', 9)).pack(pady=10)
    splash.update()
    from modules.app import MaintenanceToolbox
    app = MaintenanceToolbox(root)
    center_window(root, 1280, 820)
    splash.destroy()
    root.deiconify()
    root.mainloop()


def main():
    """Prefer the WebView UI and retain Tkinter as an offline-safe fallback."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, app_dir)
    try:
        from modules.web_app import start_web_app
        start_web_app()
    except Exception:
        run_tk_fallback()

if __name__ == '__main__':
    main()
