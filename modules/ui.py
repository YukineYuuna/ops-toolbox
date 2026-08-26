#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reusable UI components for the desktop toolbox."""

import tkinter as tk


def _hex_mix(first, second, ratio):
    """Blend two #RRGGBB colors without adding a rendering dependency."""
    a = tuple(int(first[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(second[i:i + 2], 16) for i in (1, 3, 5))
    ratio = max(0.0, min(1.0, ratio))
    return '#%02x%02x%02x' % tuple(
        int(a[i] + (b[i] - a[i]) * ratio) for i in range(3)
    )


class SidebarButton(tk.Frame):
    """Compact sidebar item with a persistent active rail."""

    def __init__(self, parent, category, text, icon, command, theme, active=False):
        super().__init__(parent, bg=theme['sidebar'], height=40, cursor='hand2')
        self.category = category
        self.command = command
        self.theme = theme
        self.active = active
        self.pack(fill=tk.X, padx=10, pady=2)
        self.pack_propagate(False)

        self.active_rail = tk.Frame(self, width=3, bg=self._rail_color())
        self.active_rail.pack(side=tk.LEFT, fill=tk.Y, pady=7)
        self.active_rail.pack_propagate(False)
        self.icon_lbl = tk.Label(
            self,
            text=icon,
            bg=self._bg(),
            fg=self._icon_color(),
            font=('Segoe UI Emoji', 12),
            width=2,
        )
        self.icon_lbl.pack(side=tk.LEFT, padx=(9, 5))
        self.text_lbl = tk.Label(
            self,
            text=text,
            bg=self._bg(),
            fg=self._fg(),
            font=('Microsoft YaHei', 9),
        )
        self.text_lbl.pack(side=tk.LEFT)

        for widget in (self, self.active_rail, self.icon_lbl, self.text_lbl):
            widget.bind('<Enter>', self.on_enter)
            widget.bind('<Leave>', self.on_leave)
            widget.bind('<Button-1>', self.on_click)
        self.update_colors()

    def _bg(self):
        return self.theme['sidebar_active'] if self.active else self.theme['sidebar']

    def _fg(self):
        return self.theme['fg'] if self.active else self.theme['sidebar_fg']

    def _icon_color(self):
        return self.theme['accent'] if self.active else self.theme['sidebar_fg']

    def _rail_color(self):
        return self.theme['accent'] if self.active else self.theme['sidebar']

    def on_enter(self, event=None):
        if not self.active:
            self.set_bg(self.theme['sidebar_hover'])
            self.icon_lbl.configure(fg=self.theme['fg'])

    def on_leave(self, event=None):
        self.update_colors()

    def on_click(self, event=None):
        self.command()

    def set_active(self, active):
        self.active = active
        self.update_colors()

    def set_bg(self, color):
        self.configure(bg=color)
        self.icon_lbl.configure(bg=color)
        self.text_lbl.configure(bg=color)

    def update_colors(self):
        self.set_bg(self._bg())
        self.active_rail.configure(bg=self._rail_color())
        self.icon_lbl.configure(fg=self._icon_color())
        self.text_lbl.configure(fg=self._fg())

    def refresh_theme(self, theme):
        self.theme = theme
        self.update_colors()


class ModernTooltip:
    """Small tooltip for icon-only actions."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind('<Enter>', self.show, add='+')
        widget.bind('<Leave>', self.hide, add='+')

    def show(self, event=None):
        if self.tip or not self.widget.winfo_exists():
            return
        x = self.widget.winfo_rootx() + 8
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_attributes('-topmost', True)
        self.tip.configure(bg='#0b1016')
        tk.Label(
            self.tip,
            text=self.text,
            bg='#0b1016',
            fg='#e7edf5',
            font=('Microsoft YaHei', 8),
            padx=9,
            pady=5,
        ).pack()
        self.tip.wm_geometry('+{}+{}'.format(x, y))

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class ActionCard(tk.Frame):
    """Dense, scan-friendly tool card with icon actions."""

    def __init__(self, parent, task, app, theme, wrap=260):
        super().__init__(
            parent,
            bg=theme['card'],
            highlightbackground=theme['card_border'],
            highlightthickness=1,
            cursor='hand2',
            height=136,
        )
        self.task = task
        self.app = app
        self.theme = theme
        self.pack_propagate(False)

        body = tk.Frame(self, bg=theme['card'])
        body.pack(fill=tk.BOTH, expand=True, padx=11, pady=10)

        header = tk.Frame(body, bg=theme['card'])
        header.pack(fill=tk.X)
        icon_tile = tk.Frame(header, bg=theme.get('icon_bg', theme['sidebar_active']), width=34, height=34)
        icon_tile.pack(side=tk.LEFT)
        icon_tile.pack_propagate(False)
        tk.Label(
            icon_tile,
            text=task.get('icon', '🔧'),
            bg=theme.get('icon_bg', theme['sidebar_active']),
            fg=theme['accent'],
            font=('Segoe UI Emoji', 15),
        ).pack(fill=tk.BOTH, expand=True)

        title_box = tk.Frame(header, bg=theme['card'])
        title_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(9, 0))
        tk.Label(
            title_box,
            text=task['name'],
            bg=theme['card'],
            fg=theme['fg'],
            font=('Microsoft YaHei', 10, 'bold'),
            anchor='w',
        ).pack(fill=tk.X)
        tk.Label(
            title_box,
            text=app._category_label(task.get('category', '')).replace(task.get('icon', ''), '').strip(),
            bg=theme['card'],
            fg=theme['muted'],
            font=('Microsoft YaHei', 8),
            anchor='w',
        ).pack(fill=tk.X, pady=(1, 0))

        desc = tk.Label(
            body,
            text=task['desc'],
            bg=theme['card'],
            fg=theme['muted'],
            font=('Microsoft YaHei', 8),
            wraplength=wrap,
            justify=tk.LEFT,
            anchor='nw',
            height=2,
        )
        desc.pack(fill=tk.X, pady=(7, 3))

        footer = tk.Frame(body, bg=theme['card'])
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        tag_box = tk.Frame(footer, bg=theme['card'])
        tag_box.pack(side=tk.LEFT)
        self._add_tag(tag_box, task.get('danger'), '风险', theme['error'])
        self._add_tag(tag_box, task.get('admin'), '管理员', theme['warning'])
        self._add_tag(tag_box, task.get('reboot'), '重启', theme['info'])

        self.star_btn = self._icon_button(footer, '☆', '收藏/取消收藏', self.toggle_star)
        self.star_btn.configure(fg=theme['warning'])
        self.star_btn.pack(side=tk.RIGHT, padx=(4, 0))
        self.detail_btn = self._icon_button(footer, 'ⓘ', '查看详情', self.show_detail)
        self.detail_btn.pack(side=tk.RIGHT, padx=(4, 0))
        self.run_btn = self._icon_button(footer, '▶', '运行工具', self.run, primary=True)
        self.run_btn.pack(side=tk.RIGHT, padx=(4, 0))
        self.update_star()

        self._hover_widgets = []
        self._bind_widgets = []
        self._collect_card_widgets(self)
        for widget in [self] + self._bind_widgets:
            widget.bind('<Enter>', self._on_card_enter, add='+')
            widget.bind('<Leave>', self._on_card_leave, add='+')
        for widget in [self] + self._hover_widgets:
            if widget not in (self.star_btn, self.detail_btn, self.run_btn):
                widget.bind('<Button-1>', self.show_detail, add='+')
        self._inside = False

    def _add_tag(self, parent, enabled, text, color):
        if not enabled:
            return
        tk.Label(
            parent,
            text=text,
            bg=self.theme.get('tag_bg', self.theme['sidebar_active']),
            fg=color,
            font=('Microsoft YaHei', 7),
            padx=4,
            pady=1,
        ).pack(side=tk.LEFT, padx=(0, 3))

    def _icon_button(self, parent, text, tooltip, command, primary=False):
        background = self.theme['accent'] if primary else self.theme['sidebar_active']
        foreground = self.theme['accent_fg'] if primary else self.theme['muted']
        button = tk.Label(
            parent,
            text=text,
            bg=background,
            fg=foreground,
            font=('Segoe UI Symbol', 9, 'bold'),
            width=3,
            pady=2,
            cursor='hand2',
        )
        hover = self.theme['accent_hover'] if primary else self.theme['sidebar_hover']
        button.bind('<Enter>', lambda event: button.configure(bg=hover, fg=self.theme['fg']))
        button.bind('<Leave>', lambda event: button.configure(bg=background, fg=foreground))
        button.bind('<Button-1>', command)
        ModernTooltip(button, tooltip)
        return button

    def _collect_card_widgets(self, widget):
        for child in widget.winfo_children():
            self._bind_widgets.append(child)
            try:
                if child.cget('bg') == self.theme['card']:
                    self._hover_widgets.append(child)
            except tk.TclError:
                pass
            self._collect_card_widgets(child)

    def _on_card_enter(self, event=None):
        if self._inside:
            return
        self._inside = True
        hover = self.theme['card_hover']
        self.configure(bg=hover, highlightbackground=self.theme['accent'])
        for widget in self._hover_widgets:
            try:
                widget.configure(bg=hover)
            except tk.TclError:
                pass

    def _on_card_leave(self, event=None):
        self.after_idle(self._finish_leave)

    def _finish_leave(self):
        try:
            x, y = self.winfo_pointerxy()
            target = self.winfo_containing(x, y)
        except tk.TclError:
            return
        while target:
            if target == self:
                return
            target = getattr(target, 'master', None)
        self._inside = False
        self.configure(bg=self.theme['card'], highlightbackground=self.theme['card_border'])
        for widget in self._hover_widgets:
            try:
                widget.configure(bg=self.theme['card'])
            except tk.TclError:
                pass

    def toggle_star(self, event=None):
        self.app.toggle_favorite(self.task['id'])

    def update_star(self):
        selected = self.task['id'] in self.app.config.get('favorites', [])
        self.star_btn.configure(text='★' if selected else '☆')

    def show_detail(self, event=None):
        self.app.show_task_detail(self.task)

    def run(self, event=None):
        self.app.run_function(self.task)


class GradientBanner(tk.Canvas):
    """A rounded, layered status banner that approximates glass in Tk."""

    def __init__(self, parent, height=100, start='#43c6ac', end='#257a8a', icon='', title='', subtitle=''):
        self._parent_bg = parent.cget('bg')
        super().__init__(
            parent,
            height=height,
            bg=self._parent_bg,
            highlightthickness=0,
            bd=0,
        )
        self._start = start
        self._end = end
        self._icon = icon
        self._title = title
        self._subtitle = subtitle
        self.bind('<Configure>', self._redraw)

    def _round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, splinesteps=18, **kwargs)

    def _redraw(self, event=None):
        self.delete('all')
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 2 or height <= 2:
            return

        base = _hex_mix(_hex_mix(self._start, self._end, 0.45), '#071019', 0.72)
        edge = _hex_mix(self._start, '#ffffff', 0.18)
        self._round_rect(1, 1, width - 1, height - 1, 14, fill=base, outline=edge, width=1)

        grid = _hex_mix(base, '#ffffff', 0.06)
        for x in range(32, width, 54):
            self.create_line(x, 12, x, height - 12, fill=grid)
        for y in range(20, height, 28):
            self.create_line(12, y, width - 12, y, fill=grid)
        self.create_rectangle(1, 1, 5, height - 1, fill=self._start, outline='')

        icon_x = 28
        if self._icon:
            self.create_text(icon_x, height / 2, text=self._icon, font=('Segoe UI Emoji', 24), fill='#ffffff', anchor='w')
            icon_x += 52
        self.create_text(
            icon_x,
            height / 2 - 13,
            text=self._title,
            font=('Microsoft YaHei', 14, 'bold'),
            fill='#f7fbff',
            anchor='w',
        )
        if self._subtitle:
            self.create_text(
                icon_x,
                height / 2 + 14,
                text=self._subtitle,
                font=('Microsoft YaHei', 9),
                fill='#aebdca',
                anchor='w',
            )

        badge_width = 88
        if width > 520:
            self._round_rect(width - badge_width - 24, height / 2 - 15, width - 24, height / 2 + 15, 10,
                             fill=_hex_mix(base, '#ffffff', 0.09), outline=edge, width=1)
            self.create_text(width - badge_width / 2 - 24, height / 2, text='系统就绪',
                             font=('Microsoft YaHei', 7, 'bold'), fill=self._start)
