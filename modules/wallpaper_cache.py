#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validated, persistent cache for API-provided wallpapers."""
from __future__ import annotations

import hashlib
import http.cookiejar
import io
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError


WALLPAPER_API_URL = os.environ.get(
    "TOOLBOX_WALLPAPER_API_URL",
    "https://api.r10086.com/%E6%A8%B1%E9%81%93%E9%9A%8F%E6%9C%BA%E5%9B%BE%E7%89%87api%E6%8E%A5%E5%8F%A3.php",
).strip()
MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024
CACHE_LIMIT = 8
AUTO_REFRESH_SECONDS = 6 * 60 * 60
MANUAL_TRIGGER_ATTEMPTS = 6
AUTO_TRIGGER_ATTEMPTS = 2
MANUAL_TRIGGER_BUDGET_SECONDS = 18
AUTO_TRIGGER_BUDGET_SECONDS = 8
TRIGGER_DELAY_SECONDS = 0.35
TARGET_SIZE = (1920, 1080)


class WallpaperCache:
    def __init__(self, config_dir: Path, bundled_wallpapers: list[dict]):
        self.cache_dir = config_dir / "wallpapers"
        self.state_file = self.cache_dir / "sync-state.json"
        self.bundled_wallpapers = list(bundled_wallpapers)
        self._lock = threading.Lock()

    def list_wallpapers(self) -> list[dict]:
        cached = []
        try:
            files = sorted(
                self.cache_dir.glob("api-*.webp"),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
        except OSError:
            files = []
        for path in files[:CACHE_LIMIT]:
            try:
                timestamp = time.strftime("%m-%d %H:%M", time.localtime(path.stat().st_mtime))
                cached.append({
                    "id": path.stem,
                    "file": path.resolve().as_uri(),
                    "name": "API 缓存 · {}".format(timestamp),
                    "source": "api-cache",
                })
            except OSError:
                continue
        return cached + list(self.bundled_wallpapers)

    def refresh(self, force: bool = False) -> dict:
        if not self._lock.acquire(blocking=False):
            return {"ok": False, "message": "壁纸正在更新，请稍候"}
        try:
            if not force and not self._refresh_due():
                return {"ok": True, "downloaded": False, "message": "壁纸缓存已是最新"}
            return self._trigger_refresh(force)
        finally:
            self._lock.release()

    def _trigger_refresh(self, force: bool) -> dict:
        max_attempts = MANUAL_TRIGGER_ATTEMPTS if force else AUTO_TRIGGER_ATTEMPTS
        budget = MANUAL_TRIGGER_BUDGET_SECONDS if force else AUTO_TRIGGER_BUDGET_SECONDS
        deadline = time.monotonic() + budget
        attempts_made = 0
        duplicates = 0
        valid_payloads = set()
        last_error = None

        for attempt in range(1, max_attempts + 1):
            remaining = deadline - time.monotonic()
            if remaining < 1:
                break
            attempts_made += 1
            try:
                payload = self._download_once(attempt, timeout=min(6, max(2, remaining)))
                payload_digest = hashlib.sha256(payload).hexdigest()
                if payload_digest in valid_payloads:
                    duplicates += 1
                else:
                    normalized, digest = self._normalize(payload)
                    valid_payloads.add(payload_digest)
                    if not self._is_known_digest(digest):
                        self.cache_dir.mkdir(parents=True, exist_ok=True)
                        destination = self.cache_dir / "api-{}.webp".format(digest[:16])
                        temporary = destination.with_suffix(".tmp")
                        temporary.write_bytes(normalized)
                        temporary.replace(destination)
                        self._prune()
                        self._write_sync_state(True)
                        return {
                            "ok": True,
                            "downloaded": True,
                            "attempts": attempts_made,
                            "duplicates": duplicates,
                            "current_id": destination.stem,
                            "message": "第 {} 次访问后获取到新壁纸".format(attempts_made),
                        }
                    duplicates += 1
            except (
                OSError,
                RuntimeError,
                ValueError,
                urllib.error.URLError,
                UnidentifiedImageError,
                Image.DecompressionBombError,
            ) as exc:
                last_error = exc

            if attempt < max_attempts:
                remaining = deadline - time.monotonic()
                if remaining > 1:
                    time.sleep(min(TRIGGER_DELAY_SECONDS, remaining - 1))

        if valid_payloads:
            self._write_sync_state(True)
            return {
                "ok": True,
                "downloaded": False,
                "attempts": attempts_made,
                "duplicates": duplicates,
                "message": "已连续访问接口 {} 次，但服务端仍返回同一张图".format(attempts_made),
            }

        self._write_sync_state(False)
        return {
            "ok": False,
            "downloaded": False,
            "attempts": attempts_made,
            "duplicates": duplicates,
            "message": "壁纸接口暂不可用，已继续使用本地缓存",
            "detail": str(last_error or "下载失败"),
        }

    def _refresh_due(self) -> bool:
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
            return time.time() - float(state.get("last_attempt", 0)) >= AUTO_REFRESH_SECONDS
        except (OSError, ValueError, TypeError):
            return True

    def _write_sync_state(self, success: bool) -> None:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            temporary = self.state_file.with_suffix(".tmp")
            temporary.write_text(
                json.dumps({"last_attempt": time.time(), "success": bool(success)}),
                encoding="utf-8",
            )
            temporary.replace(self.state_file)
        except OSError:
            pass

    @staticmethod
    def _download_once(attempt: int, timeout: float) -> bytes:
        nonce = uuid.uuid4().hex
        parts = urllib.parse.urlsplit(WALLPAPER_API_URL)
        original_query = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
        trigger_query = [
            ("ops_session", nonce),
            ("ops_attempt", str(attempt)),
            ("_", "{}-{}".format(int(time.time() * 1000), nonce[:8])),
        ]
        query = trigger_query + original_query if attempt % 2 == 0 else original_query + trigger_query
        url = urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.5",
                "Accept-Encoding": "identity",
                "Cache-Control": "no-cache, no-store, max-age=0",
                "Pragma": "no-cache",
                "Connection": "close",
                "Cookie": "ops_wallpaper_session={}".format(nonce),
                "Referer": "https://api.r10086.com/",
                "User-Agent": "Mozilla/5.0 OpsToolbox/3.1 session/{}".format(nonce[:8]),
            },
        )
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        )
        with opener.open(request, timeout=timeout) as response:
            if not response.geturl().lower().startswith("https://"):
                raise RuntimeError("壁纸接口跳转到了非 HTTPS 地址")
            content_type = response.headers.get_content_type()
            if not content_type.startswith("image/"):
                raise RuntimeError("壁纸接口未返回图片")
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > MAX_DOWNLOAD_BYTES:
                raise RuntimeError("壁纸文件超过大小限制")
            payload = response.read(MAX_DOWNLOAD_BYTES + 1)
            if len(payload) > MAX_DOWNLOAD_BYTES:
                raise RuntimeError("壁纸文件超过大小限制")
            return payload

    @staticmethod
    def _normalize(payload: bytes) -> tuple[bytes, str]:
        with Image.open(io.BytesIO(payload)) as source:
            source.seek(0)
            if source.width < 1280 or source.height < 720:
                raise ValueError("壁纸分辨率低于 1280×720")
            if source.width * source.height > 40_000_000:
                raise ValueError("壁纸像素尺寸超过安全限制")
            image = ImageOps.exif_transpose(source).convert("RGB")
            image = ImageOps.fit(image, TARGET_SIZE, method=Image.Resampling.LANCZOS)
            output = io.BytesIO()
            image.save(output, format="WEBP", quality=88, method=6)
        normalized = output.getvalue()
        return normalized, hashlib.sha256(normalized).hexdigest()

    def _is_known_digest(self, digest: str) -> bool:
        short = digest[:16]
        for item in self.bundled_wallpapers:
            if str(item.get("id", "")).endswith(short):
                return True
        return any(path.stem.endswith(short) for path in self.cache_dir.glob("api-*.webp"))

    def _prune(self) -> None:
        try:
            files = sorted(
                self.cache_dir.glob("api-*.webp"),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
        except OSError:
            return
        for path in files[CACHE_LIMIT:]:
            try:
                path.unlink()
            except OSError:
                pass
