#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local pywebview bridge for the offline-first toolbox UI."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from modules import utils
from modules.platform_detect import APP_NAME, IS_LINUX, IS_MAC, IS_WINDOWS, PLATFORM_LABEL
from modules.wallpaper_cache import WallpaperCache

if IS_WINDOWS:
    from modules import data as data_module
elif IS_MAC:
    from modules import data_mac as data_module
else:
    from modules import data_linux as data_module

try:
    import psutil
except ImportError:  # Packaged fallback; the UI still starts without live gauges.
    psutil = None


APP_VERSION = "v3.1"
PLATFORM_KEY = "windows" if IS_WINDOWS else "macos" if IS_MAC else "linux"
BUNDLED_WALLPAPERS = [
    {
        "id": "api-offline-b51a492d53e703b7",
        "file": "assets/wallpapers/api-offline-b51a492d53e703b7.webp",
        "name": "樱道离线缓存",
        "source": "api-offline",
    },
]
DEFAULT_CATEGORIES = [
    ("network", "网络修复", "network"),
    ("system", "系统修复", "shield-check"),
    ("cleanup", "清理工具", "sparkles"),
    ("boot", "启动修复", "power"),
    ("optimize", "性能优化", "gauge"),
    ("info", "系统信息", "chart-no-axes-column"),
    ("tools", "系统工具", "wrench"),
]


def _config_dir() -> Path:
    if IS_WINDOWS:
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return root / "OpsToolbox"
    if IS_MAC:
        return Path.home() / "Library" / "Application Support" / "OpsToolbox"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "ops-toolbox"


DEFAULT_CONFIG = {
    "theme": "dark",
    "font_scale": 1.08,
    "wallpaper": 0,
    "wallpaper_id": "api-offline-b51a492d53e703b7",
    "wallpaper_auto": True,
    "wallpaper_interval": 45,
    "favorites": [],
    "recent": [],
    "ai": {
        "provider": "offline",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "model": "openrouter/free",
        "remember_key": False,
    },
}


class WebBridge:
    def __init__(self):
        self.functions = list(data_module.FUNCTIONS)
        self.by_id = {tool["id"]: tool for tool in self.functions}
        self.categories = self._categories()
        self.config_dir = _config_dir()
        self.config_file = self.config_dir / "config.json"
        self.secret_file = self.config_dir / "ai-secret.json"
        self.config = self._load_config()
        self.wallpaper_cache = WallpaperCache(self.config_dir, BUNDLED_WALLPAPERS)
        self._session_api_key = ""
        self._lock = threading.RLock()
        self._logs = []
        self._log_seq = 0
        self._running = None
        self._last_result = None

    def _categories(self):
        source = getattr(data_module, "CATEGORIES", DEFAULT_CATEGORIES)
        icon_map = {
            "network": "network", "cleanup": "sparkles", "optimize": "gauge",
            "info": "chart-no-axes-column", "tools": "wrench", "system": "shield-check",
            "boot": "power", "security": "shield", "storage": "hard-drive",
            "services": "workflow", "packages": "package-check", "diagnose": "stethoscope",
        }
        return [
            {"id": item[0], "label": item[1], "icon": icon_map.get(item[0], "boxes")}
            for item in source
        ]

    def _load_config(self):
        cfg = json.loads(json.dumps(DEFAULT_CONFIG))
        legacy = Path(__file__).with_name("toolbox_config.json")
        for path in (legacy, self.config_file):
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                for key, value in loaded.items():
                    if key == "ai" and isinstance(value, dict):
                        cfg["ai"].update(value)
                    else:
                        cfg[key] = value
            except (OSError, ValueError, TypeError):
                continue
        return cfg

    def _save_config(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.config_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.config_file)

    def _tool_public(self, tool):
        return {
            key: tool.get(key)
            for key in ("id", "name", "desc", "category", "danger", "admin", "reboot")
        } | {"icon": self._tool_icon(tool)}

    @staticmethod
    def _tool_icon(tool):
        mapping = {
            "network": "wifi", "system": "shield-check", "cleanup": "trash-2",
            "boot": "power", "optimize": "zap", "info": "monitor-cog", "tools": "wrench",
            "security": "shield", "storage": "hard-drive", "services": "workflow",
            "packages": "package-check",
        }
        return mapping.get(tool.get("category"), "circle-wrench")

    def get_bootstrap(self):
        counts = {cat["id"]: 0 for cat in self.categories}
        for tool in self.functions:
            counts[tool.get("category")] = counts.get(tool.get("category"), 0) + 1
        return {
            "app_name": APP_NAME,
            "version": APP_VERSION,
            "platform": PLATFORM_KEY,
            "platform_label": PLATFORM_LABEL,
            "is_admin": bool(utils.is_admin()),
            "tools": [self._tool_public(tool) for tool in self.functions],
            "categories": self.categories,
            "counts": counts,
            "config": self._public_config(),
            "wallpapers": self.wallpaper_cache.list_wallpapers(),
        }

    def _public_config(self):
        cfg = json.loads(json.dumps(self.config))
        cfg["ai"]["has_key"] = bool(self._get_api_key())
        return cfg

    def save_settings(self, updates):
        if not isinstance(updates, dict):
            return {"ok": False, "message": "设置格式无效"}
        validators = {
            "theme": lambda v: v if v in ("dark", "light") else None,
            "font_scale": lambda v: max(0.85, min(1.4, float(v))),
            "wallpaper": lambda v: max(0, min(len(self.wallpaper_cache.list_wallpapers()) - 1, int(v))),
            "wallpaper_auto": bool,
            "wallpaper_interval": lambda v: max(15, min(300, int(v))),
        }
        for key, validator in validators.items():
            if key not in updates:
                continue
            try:
                value = validator(updates[key])
                if value is not None:
                    self.config[key] = value
            except (TypeError, ValueError):
                pass
        if "wallpaper_id" in updates:
            wallpaper_id = str(updates.get("wallpaper_id") or "")
            valid_ids = {item["id"] for item in self.wallpaper_cache.list_wallpapers()}
            if wallpaper_id in valid_ids:
                self.config["wallpaper_id"] = wallpaper_id
        self._save_config()
        return {"ok": True, "config": self._public_config()}

    def refresh_wallpapers(self, force=False):
        result = self.wallpaper_cache.refresh(bool(force))
        result["wallpapers"] = self.wallpaper_cache.list_wallpapers()
        return result

    def toggle_favorite(self, tool_id):
        if tool_id not in self.by_id:
            return {"ok": False}
        favorites = list(self.config.get("favorites", []))
        if tool_id in favorites:
            favorites.remove(tool_id)
            active = False
        else:
            favorites.insert(0, tool_id)
            active = True
        self.config["favorites"] = favorites
        self._save_config()
        return {"ok": True, "active": active, "favorites": favorites}

    def system_snapshot(self):
        if psutil is None:
            return {"cpu": None, "memory": None, "disk": None, "uptime": "未知", "network": False}
        try:
            disk_path = os.environ.get("SystemDrive", "C:") + "\\" if IS_WINDOWS else "/"
            net = any(item.isup for item in psutil.net_if_stats().values())
            return {
                "cpu": round(psutil.cpu_percent(interval=0.15)),
                "memory": round(psutil.virtual_memory().percent),
                "disk": round(psutil.disk_usage(disk_path).percent),
                "uptime": utils.format_seconds(time.time() - psutil.boot_time()),
                "network": net,
            }
        except Exception:
            return {"cpu": None, "memory": None, "disk": None, "uptime": "未知", "network": False}

    def run_tool(self, tool_id, confirmed=False):
        tool = self.by_id.get(tool_id)
        if not tool:
            return {"ok": False, "message": "找不到该工具"}
        if tool.get("danger") and not confirmed:
            return {
                "ok": False,
                "needs_confirmation": True,
                "message": "“{}”会修改系统设置或数据，确认继续？".format(tool["name"]),
            }
        if IS_WINDOWS and tool.get("admin") and not utils.is_admin():
            return {"ok": False, "needs_admin": True, "message": "该操作需要管理员权限"}
        with self._lock:
            if self._running:
                return {"ok": False, "busy": True, "message": "已有任务正在运行"}
            self._running = {"id": tool_id, "name": tool["name"], "started": time.time()}
            self._last_result = None
        self._add_recent(tool_id)
        threading.Thread(target=self._tool_worker, args=(tool,), daemon=True).start()
        return {"ok": True, "started": True, "tool": self._tool_public(tool)}

    def _tool_worker(self, tool):
        self._log("开始执行：{}".format(tool["name"]), "title")
        ok = False
        try:
            ok = bool(tool["func"](log=self._log))
            self._log("{}：{}".format(tool["name"], "执行成功" if ok else "执行完成，结果可能不完整"), "success" if ok else "warning")
        except Exception as exc:
            self._log("{}：执行失败 - {}".format(tool["name"], exc), "error")
        finally:
            with self._lock:
                self._last_result = {"id": tool["id"], "ok": ok, "finished": time.time()}
                self._running = None

    def _add_recent(self, tool_id):
        recent = list(self.config.get("recent", []))
        if tool_id in recent:
            recent.remove(tool_id)
        recent.insert(0, tool_id)
        self.config["recent"] = recent[:12]
        self._save_config()

    def _log(self, message, level="info"):
        if not message:
            return
        with self._lock:
            self._log_seq += 1
            self._logs.append({
                "seq": self._log_seq,
                "time": time.strftime("%H:%M:%S"),
                "level": level,
                "message": str(message),
            })
            self._logs = self._logs[-300:]

    def get_activity(self, after=0):
        try:
            after = int(after)
        except (TypeError, ValueError):
            after = 0
        with self._lock:
            return {
                "running": self._running,
                "last_result": self._last_result,
                "logs": [item for item in self._logs if item["seq"] > after],
            }

    def elevate(self):
        if not IS_WINDOWS:
            return {"ok": False, "message": "当前系统会在执行时请求授权"}
        ok = utils.run_as_admin()
        return {"ok": bool(ok), "message": "已请求管理员权限" if ok else "无法发起权限提升"}

    def set_ai_settings(self, settings):
        if not isinstance(settings, dict):
            return {"ok": False, "message": "AI 设置无效"}
        provider = settings.get("provider", "offline")
        if provider not in ("offline", "ollama", "openai"):
            provider = "offline"
        ai = self.config.setdefault("ai", {})
        ai["provider"] = provider
        ai["endpoint"] = str(settings.get("endpoint") or ai.get("endpoint") or "").strip()
        ai["model"] = str(settings.get("model") or ai.get("model") or "").strip()
        remember = bool(settings.get("remember_key"))
        ai["remember_key"] = remember
        key = str(settings.get("api_key") or "").strip()
        if key:
            self._session_api_key = key
        self._save_config()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if remember and key:
            self.secret_file.write_text(json.dumps({"api_key": key}), encoding="utf-8")
            try:
                os.chmod(self.secret_file, 0o600)
            except OSError:
                pass
        elif not remember and self.secret_file.exists():
            try:
                self.secret_file.unlink()
            except OSError:
                pass
        return {"ok": True, "ai": self._public_config()["ai"]}

    def _get_api_key(self):
        if self._session_api_key:
            return self._session_api_key
        env_key = os.environ.get("TOOLBOX_AI_API_KEY", "")
        if env_key:
            return env_key
        if self.config.get("ai", {}).get("remember_key"):
            try:
                return json.loads(self.secret_file.read_text(encoding="utf-8")).get("api_key", "")
            except (OSError, ValueError, TypeError):
                pass
        return ""

    def ask_assistant(self, message):
        message = str(message or "").strip()
        if not message:
            return {"ok": False, "message": "请输入问题"}
        offline = self._offline_answer(message)
        ai = self.config.get("ai", {})
        provider = ai.get("provider", "offline")
        if provider == "offline":
            return offline
        try:
            if provider == "ollama":
                answer = self._ask_ollama(message, offline["suggestions"])
                mode = "Ollama 本地模型"
            else:
                answer = self._ask_openai(message, offline["suggestions"])
                mode = "在线模型"
            return {"ok": True, "mode": mode, "answer": answer, "suggestions": offline["suggestions"]}
        except Exception as exc:
            offline["answer"] = "联网/本地模型暂不可用，已切换离线诊断。\n\n" + offline["answer"]
            offline["fallback_reason"] = str(exc)
            return offline

    def _offline_answer(self, message):
        text = message.lower()
        groups = {
            "network": "网络 断网 上不了网 网卡 wifi dns ip 延迟 丢包 网页",
            "cleanup": "磁盘 空间 满了 垃圾 缓存 临时文件 清理 大文件",
            "optimize": "卡顿 很慢 cpu 内存 性能 风扇 发热 动画",
            "boot": "开机 启动 黑屏 重启 引导 安全模式",
            "system": "系统 损坏 更新 报错 蓝屏 文件 修复",
            "info": "查看 信息 配置 版本 日志 错误 驱动 软件 服务",
            "security": "安全 防火墙 filevault gatekeeper 权限",
            "storage": "磁盘 硬盘 smart 文件系统 容量",
            "services": "服务 systemd launchctl 进程 自启动",
            "packages": "更新 软件包 apt dnf pacman brew homebrew",
        }
        scored = []
        for tool in self.functions:
            score = 0
            haystack = "{} {} {}".format(tool["name"], tool["desc"], tool["id"]).lower()
            for token in set(text.replace("，", " ").replace("。", " ").split()):
                if len(token) > 1 and token in haystack:
                    score += 4
            for category, words in groups.items():
                if tool.get("category") == category and any(word in text for word in words.split()):
                    score += 3
            for keyword in ("dns", "wifi", "ip", "cpu", "内存", "磁盘", "日志", "启动", "更新", "缓存", "防火墙", "服务"):
                if keyword in text and keyword in haystack:
                    score += 5
            if score:
                scored.append((score, tool))
        scored.sort(key=lambda item: (-item[0], bool(item[1].get("danger")), item[1]["name"]))
        picks = [self._tool_public(item[1]) for item in scored[:5]]
        if picks:
            names = "、".join(item["name"] for item in picks[:3])
            answer = "根据描述，建议先从只读检查或低风险项目开始：{}。查看每个工具的说明后再运行；标有“有风险”的操作会再次确认。".format(names)
        else:
            answer = "暂时无法准确定位。可以补充出现时间、报错文字、是否能联网、磁盘剩余空间，以及最近是否安装过更新或软件。"
        return {"ok": True, "mode": "离线诊断", "answer": answer, "suggestions": picks}

    def _tool_context(self, suggestions):
        if not suggestions:
            return "当前没有高置信度候选工具。"
        return "\n".join("- {id}: {name}；{desc}".format(**item) for item in suggestions)

    def _ask_ollama(self, message, suggestions):
        ai = self.config.get("ai", {})
        endpoint = ai.get("endpoint") or "http://127.0.0.1:11434/api/chat"
        if "11434" not in endpoint:
            endpoint = "http://127.0.0.1:11434/api/chat"
        payload = {
            "model": ai.get("model") or "qwen2.5:3b",
            "stream": False,
            "messages": [
                {"role": "system", "content": "你是桌面运维助手。只能推荐给出的工具，不要编造工具，不要声称已经执行。回答简洁、先低风险检查。"},
                {"role": "user", "content": "用户问题：{}\n可用候选：\n{}".format(message, self._tool_context(suggestions))},
            ],
        }
        data = self._post_json(endpoint, payload, {}, timeout=20)
        return data.get("message", {}).get("content") or "本地模型未返回内容"

    def _ask_openai(self, message, suggestions):
        ai = self.config.get("ai", {})
        endpoint = ai.get("endpoint") or "https://openrouter.ai/api/v1/chat/completions"
        if not endpoint.startswith("https://"):
            raise ValueError("在线接口必须使用 HTTPS")
        key = self._get_api_key()
        if not key:
            raise ValueError("尚未配置 API Key")
        payload = {
            "model": ai.get("model") or "openrouter/free",
            "messages": [
                {"role": "system", "content": "你是桌面运维助手。仅根据候选工具给建议，不要编造工具，不要声称已执行命令。优先只读和低风险操作，用中文简短回答。"},
                {"role": "user", "content": "系统：{}\n问题：{}\n候选工具：\n{}".format(PLATFORM_LABEL, message, self._tool_context(suggestions))},
            ],
            "temperature": 0.2,
        }
        headers = {"Authorization": "Bearer " + key, "User-Agent": "OpsToolbox/3.1"}
        data = self._post_json(endpoint, payload, headers, timeout=25)
        return data.get("choices", [{}])[0].get("message", {}).get("content") or "在线模型未返回内容"

    @staticmethod
    def _post_json(url, payload, headers, timeout):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=body, method="POST")
        request.add_header("Content-Type", "application/json")
        for key, value in headers.items():
            request.add_header(key, value)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read(300).decode("utf-8", errors="replace")
            raise RuntimeError("接口返回 HTTP {}：{}".format(exc.code, detail)) from exc

    def open_config_folder(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            if IS_WINDOWS:
                os.startfile(str(self.config_dir))
            elif IS_MAC:
                subprocess.Popen(["open", str(self.config_dir)])
            else:
                subprocess.Popen(["xdg-open", str(self.config_dir)])
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    def runtime_status(self):
        return {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "ollama": bool(shutil.which("ollama")),
            "config_dir": str(self.config_dir),
        }
