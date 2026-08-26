#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pywebview host for the responsive desktop interface."""
import os
import sys
from pathlib import Path

from modules.platform_detect import APP_NAME, IS_WINDOWS
from modules.web_bridge import APP_VERSION, WebBridge


def _bundle_root():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def start_web_app():
    import webview

    index = _bundle_root() / "web" / "index.html"
    if not index.exists():
        raise FileNotFoundError("Web UI assets are missing: {}".format(index))

    bridge = WebBridge()
    webview.create_window(
        "{} {}".format(APP_NAME, APP_VERSION),
        url=index.as_uri(),
        js_api=bridge,
        width=1440,
        height=900,
        min_size=(980, 680),
        background_color="#091016",
        text_select=False,
    )
    options = {"debug": os.environ.get("TOOLBOX_WEB_DEBUG") == "1", "private_mode": False}
    if IS_WINDOWS:
        webview.start(gui="edgechromium", **options)
    else:
        webview.start(**options)

