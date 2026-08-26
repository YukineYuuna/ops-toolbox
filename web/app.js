/* global lucide */
(() => {
  "use strict";

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const state = {
    boot: null,
    view: "dashboard",
    search: "",
    activeTool: null,
    wallpaper: 0,
    wallpaperLayer: 0,
    wallpaperTimer: null,
    logAfter: 0,
    localLogs: [],
    pendingConfirm: null,
    initialized: false,
  };

  const isBrowserMode = () => !(window.pywebview && window.pywebview.api);
  const browserPlatform = () => {
    const saved = localStorage.getItem("ops-toolbox-platform");
    if (saved && ["windows", "macos", "linux"].includes(saved)) return saved;
    const value = navigator.platform.toLowerCase();
    return value.includes("mac") ? "macos" : value.includes("linux") ? "linux" : "windows";
  };

  const mockBoot = {
    app_name: "Windows 运维工具箱",
    version: "v3.1 Preview",
    platform: "windows",
    platform_label: "Windows",
    is_admin: false,
    config: { theme: "dark", font_scale: 1.08, wallpaper: 0, wallpaper_id: "api-offline-b51a492d53e703b7", wallpaper_auto: true, wallpaper_interval: 45, favorites: ["flush_dns"], recent: ["system_info"], ai: { provider: "offline", endpoint: "https://openrouter.ai/api/v1/chat/completions", model: "openrouter/free", remember_key: false, has_key: false } },
    wallpapers: [
      { id: "api-offline-b51a492d53e703b7", file: "assets/wallpapers/api-offline-b51a492d53e703b7.webp", name: "樱道离线缓存", source: "api-offline" },
    ],
    categories: [
      { id: "network", label: "网络修复", icon: "network" },
      { id: "system", label: "系统修复", icon: "shield-check" },
      { id: "cleanup", label: "清理工具", icon: "sparkles" },
      { id: "optimize", label: "性能优化", icon: "gauge" },
      { id: "info", label: "系统信息", icon: "chart-no-axes-column" },
      { id: "tools", label: "系统工具", icon: "wrench" },
    ],
    tools: [
      { id: "flush_dns", name: "刷新 DNS 缓存", desc: "清理过期的域名解析缓存，解决部分网页无法打开的问题", category: "network", icon: "wifi", danger: false, admin: true, reboot: false },
      { id: "reset_winsock", name: "重置 Winsock", desc: "重置 Windows 网络协议栈，修复网络组件异常", category: "network", icon: "wifi", danger: true, admin: true, reboot: true },
      { id: "sfc_scannow", name: "SFC 系统文件检查", desc: "扫描并修复损坏的 Windows 系统文件", category: "system", icon: "shield-check", danger: false, admin: true, reboot: false },
      { id: "clean_temp", name: "清理临时文件", desc: "清理用户和系统临时目录中的可安全删除文件", category: "cleanup", icon: "trash-2", danger: false, admin: false, reboot: false },
      { id: "disk_analyze", name: "分析磁盘占用", desc: "查看磁盘空间和主要目录占用情况", category: "cleanup", icon: "hard-drive", danger: false, admin: false, reboot: false },
      { id: "cpu_info", name: "查看 CPU 信息", desc: "查看处理器型号、核心数和当前负载", category: "optimize", icon: "cpu", danger: false, admin: false, reboot: false },
      { id: "system_info", name: "完整系统信息", desc: "查看系统、硬件、内存、磁盘和网络摘要", category: "info", icon: "monitor-cog", danger: false, admin: false, reboot: false },
      { id: "task_manager", name: "任务管理器", desc: "打开系统任务管理器查看进程与性能", category: "tools", icon: "wrench", danger: false, admin: false, reboot: false },
    ],
  };

  const browserCatalog = {
    windows: {
      label: "Windows",
      categories: [{ id: "network", label: "网络修复", icon: "network" }, { id: "system", label: "系统修复", icon: "shield-check" }, { id: "cleanup", label: "清理工具", icon: "sparkles" }, { id: "boot", label: "启动修复", icon: "power" }, { id: "optimize", label: "性能优化", icon: "gauge" }, { id: "info", label: "系统信息", icon: "chart-no-axes-column" }, { id: "tools", label: "系统工具", icon: "wrench" }],
      tools: [{ id: "flush_dns", name: "刷新 DNS 缓存", desc: "清理 DNS 缓存，排查域名解析异常", category: "network", icon: "wifi", danger: false, admin: true, reboot: false }, { id: "reset_winsock", name: "重置 Winsock", desc: "重置 Windows 网络协议栈", category: "network", icon: "wifi", danger: true, admin: true, reboot: true }, { id: "sfc_scannow", name: "SFC 系统文件检查", desc: "扫描并修复损坏的 Windows 系统文件", category: "system", icon: "shield-check", danger: false, admin: true, reboot: false }, { id: "clean_temp", name: "清理临时文件", desc: "清理用户和系统临时目录中的可安全删除文件", category: "cleanup", icon: "trash-2", danger: false, admin: false, reboot: false }, { id: "disk_analyze", name: "分析磁盘占用", desc: "查看磁盘空间和主要目录占用情况", category: "cleanup", icon: "hard-drive", danger: false, admin: false, reboot: false }, { id: "cpu_info", name: "查看 CPU 信息", desc: "查看处理器型号、核心数和当前负载", category: "optimize", icon: "cpu", danger: false, admin: false, reboot: false }, { id: "system_info", name: "完整系统信息", desc: "查看系统、硬件、内存、磁盘和网络摘要", category: "info", icon: "monitor-cog", danger: false, admin: false, reboot: false }, { id: "task_manager", name: "任务管理器", desc: "打开系统任务管理器查看进程与性能", category: "tools", icon: "wrench", danger: false, admin: false, reboot: false }],
    },
    macos: {
      label: "macOS",
      categories: [{ id: "network", label: "网络修复", icon: "network" }, { id: "storage", label: "磁盘与备份", icon: "hard-drive" }, { id: "security", label: "安全与隐私", icon: "shield" }, { id: "services", label: "服务与启动项", icon: "workflow" }, { id: "cleanup", label: "清理工具", icon: "sparkles" }, { id: "packages", label: "软件与更新", icon: "package-check" }, { id: "optimize", label: "性能优化", icon: "gauge" }, { id: "info", label: "系统信息", icon: "chart-no-axes-column" }, { id: "tools", label: "系统工具", icon: "wrench" }],
      tools: [{ id: "flush_dns", name: "清理 DNS 缓存", desc: "使用 dscacheutil 与 mDNSResponder 排查解析异常", category: "network", icon: "wifi", danger: false, admin: true, reboot: false }, { id: "check_disk_layout", name: "APFS 磁盘布局", desc: "查看 APFS 容器、系统卷和容量", category: "storage", icon: "hard-drive", danger: false, admin: false, reboot: false }, { id: "check_filevault_mac", name: "FileVault 状态", desc: "检查启动磁盘加密状态", category: "security", icon: "shield", danger: false, admin: false, reboot: false }, { id: "clean_temp_files", name: "清理用户缓存", desc: "清理 ~/Library/Caches 用户缓存", category: "cleanup", icon: "trash-2", danger: false, admin: false, reboot: false }, { id: "check_cpu_info", name: "查看 CPU 信息", desc: "查看 Apple 芯片或 Intel 处理器信息", category: "optimize", icon: "cpu", danger: false, admin: false, reboot: false }, { id: "get_system_full_info", name: "完整系统信息", desc: "系统版本、CPU、内存、磁盘一览", category: "info", icon: "monitor-cog", danger: false, admin: false, reboot: false }, { id: "open_terminal", name: "打开终端", desc: "打开 macOS Terminal", category: "tools", icon: "terminal-square", danger: false, admin: false, reboot: false }],
    },
    linux: {
      label: "Linux",
      categories: [{ id: "network", label: "网络修复", icon: "network" }, { id: "storage", label: "磁盘与挂载", icon: "hard-drive" }, { id: "security", label: "安全与访问", icon: "shield" }, { id: "services", label: "服务与启动项", icon: "workflow" }, { id: "cleanup", label: "清理工具", icon: "sparkles" }, { id: "packages", label: "软件与更新", icon: "package-check" }, { id: "boot", label: "启动分析", icon: "power" }, { id: "optimize", label: "性能优化", icon: "gauge" }, { id: "info", label: "系统信息", icon: "chart-no-axes-column" }, { id: "tools", label: "系统工具", icon: "wrench" }],
      tools: [{ id: "flush_dns", name: "清理 DNS 缓存", desc: "清理 systemd-resolved、nscd 或 dnsmasq 缓存", category: "network", icon: "wifi", danger: false, admin: true, reboot: false }, { id: "check_disk_layout", name: "磁盘与挂载点", desc: "使用 lsblk 和 findmnt 查看文件系统与容量", category: "storage", icon: "hard-drive", danger: false, admin: false, reboot: false }, { id: "check_firewall_linux", name: "防火墙状态", desc: "识别 ufw、firewalld 或 nftables 当前规则", category: "security", icon: "shield", danger: false, admin: false, reboot: false }, { id: "check_failed_services_linux", name: "失败的 systemd 服务", desc: "列出启动失败的 systemd 单元", category: "services", icon: "workflow", danger: false, admin: false, reboot: false }, { id: "clean_apt_cache", name: "清理 apt 缓存", desc: "清理包缓存和无用依赖（Debian/Ubuntu）", category: "cleanup", icon: "trash-2", danger: false, admin: true, reboot: false }, { id: "check_package_updates_linux", name: "检查软件包更新", desc: "识别 apt、dnf、pacman 或 zypper 并列出更新", category: "packages", icon: "package-check", danger: false, admin: false, reboot: false }, { id: "check_cpu_info", name: "查看 CPU 信息", desc: "查看处理器型号、核心数与当前负载", category: "optimize", icon: "cpu", danger: false, admin: false, reboot: false }, { id: "get_system_full_info", name: "完整系统信息", desc: "发行版、内核、CPU、内存、磁盘一览", category: "info", icon: "monitor-cog", danger: false, admin: false, reboot: false }, { id: "open_terminal", name: "打开终端", desc: "打开系统终端模拟器", category: "tools", icon: "terminal-square", danger: false, admin: false, reboot: false }],
    },
  };

  function makeBrowserBoot() {
    const catalog = browserCatalog[browserPlatform()] || browserCatalog.windows;
    let saved = null;
    try { saved = JSON.parse(localStorage.getItem("ops-toolbox-browser-config") || "null"); } catch (_) { saved = null; }
    return { ...mockBoot, app_name: `${catalog.label} 运维工具箱`, version: "网页版", platform: browserPlatform(), platform_label: catalog.label, categories: catalog.categories, tools: catalog.tools, config: { ...mockBoot.config, ...(saved || {}), ai: { ...mockBoot.config.ai, ...((saved || {}).ai || {}) } } };
  }

  let browserBoot = null;
  const mockApi = {
    get_bootstrap: async () => (browserBoot || (browserBoot = makeBrowserBoot())),
    system_snapshot: async () => ({ cpu: null, memory: null, disk: null, uptime: "浏览器安全模式", network: navigator.onLine }),
    save_settings: async (updates) => { browserBoot.config = { ...browserBoot.config, ...updates }; localStorage.setItem("ops-toolbox-browser-config", JSON.stringify(browserBoot.config)); return { ok: true, config: browserBoot.config }; },
    toggle_favorite: async (id) => { const list = browserBoot.config.favorites || []; const active = !list.includes(id); browserBoot.config.favorites = active ? [id, ...list] : list.filter(item => item !== id); localStorage.setItem("ops-toolbox-browser-config", JSON.stringify(browserBoot.config)); return { ok: true, active, favorites: browserBoot.config.favorites }; },
    run_tool: async () => ({ ok: false, browser_mode: true, message: "网页版不会执行本机命令。请下载对应平台桌面端后再运行此工具。" }),
    get_activity: async () => ({ running: null, last_result: null, logs: [] }),
    ask_assistant: async (message) => ({ ok: true, mode: "网页版离线诊断", answer: `浏览器安全模式已根据“${message}”匹配本地工具目录。请查看建议后，在桌面端执行对应操作。`, suggestions: browserBoot.tools.slice(0, 3) }),
    set_ai_settings: async (settings) => { browserBoot.config.ai = { ...browserBoot.config.ai, ...settings }; return { ok: true }; },
    refresh_wallpapers: async () => ({ ok: true, downloaded: false, message: "网页版使用内置离线壁纸；桌面端可触发 API 缓存", wallpapers: browserBoot.wallpapers }),
    runtime_status: async () => ({ ollama: false }),
    open_config_folder: async () => ({ ok: false, message: "浏览器无法打开本机配置目录" }),
    elevate: async () => ({ ok: false, message: "网页版无法提升本机权限" }),
  };

  async function api(name, ...args) {
    const bridge = window.pywebview && window.pywebview.api;
    if (bridge && typeof bridge[name] === "function") return bridge[name](...args);
    return mockApi[name] ? mockApi[name](...args) : null;
  }

  function safe(value) {
    return String(value ?? "").replace(/[&<>'"]/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
  }

  function icons() {
    if (window.lucide) lucide.createIcons({ attrs: { "aria-hidden": "true" } });
  }

  function category(id) {
    return state.boot.categories.find(item => item.id === id) || { id, label: id, icon: "boxes" };
  }

  function setPageTitle(eyebrow, title) {
    $("#viewEyebrow").textContent = eyebrow;
    $("#viewTitle").textContent = title;
  }

  function applyTheme(theme) {
    theme = theme === "light" ? "light" : "dark";
    document.body.dataset.theme = theme;
    if (state.boot) state.boot.config.theme = theme;
    $("#themeSelect").value = theme;
  }

  function applyFontScale(scale) {
    const value = Math.max(0.85, Math.min(1.4, Number(scale) || 1.08));
    document.documentElement.style.setProperty("--font-scale", value);
    $("#fontScale").value = Math.round(value * 100);
    $("#fontScaleValue").textContent = `${Math.round(value * 100)}%`;
    if (state.boot) state.boot.config.font_scale = value;
  }

  function preloadWallpaper(file) {
    return new Promise(resolve => {
      const image = new Image();
      const timer = setTimeout(() => resolve(false), 8000);
      image.onload = () => { clearTimeout(timer); resolve(true); };
      image.onerror = () => { clearTimeout(timer); resolve(false); };
      image.src = file;
    });
  }

  async function setWallpaper(index, persist = false) {
    const list = state.boot.wallpapers;
    if (!list.length) return false;
    let loaded = false;
    for (let attempt = 0; attempt < list.length; attempt += 1) {
      index = (Number(index) + list.length) % list.length;
      loaded = await preloadWallpaper(list[index].file);
      if (loaded) break;
      index += 1;
    }
    if (!loaded) return false;
    const incoming = state.wallpaperLayer ? $("#wallpaperA") : $("#wallpaperB");
    const outgoing = state.wallpaperLayer ? $("#wallpaperB") : $("#wallpaperA");
    incoming.style.backgroundImage = `url("${list[index].file}")`;
    incoming.classList.add("active");
    outgoing.classList.remove("active");
    state.wallpaperLayer = state.wallpaperLayer ? 0 : 1;
    state.wallpaper = index;
    state.boot.config.wallpaper = index;
    state.boot.config.wallpaper_id = list[index].id;
    $("#wallpaperSelect").value = String(index);
    if (persist) api("save_settings", { wallpaper: index, wallpaper_id: list[index].id });
    return true;
  }

  function renderWallpaperOptions() {
    $("#wallpaperSelect").innerHTML = state.boot.wallpapers.map((item, index) => `<option value="${index}">${safe(item.name)}</option>`).join("");
    $("#wallpaperSelect").value = String(state.wallpaper);
  }

  async function refreshWallpapers(force = false, notify = true) {
    const button = $("#wallpaperRefresh");
    const current = state.boot.wallpapers[state.wallpaper];
    button.disabled = true;
    button.classList.add("loading");
    button.setAttribute("aria-busy", "true");
    if (force && notify) toast("正在触发壁纸接口，最多访问 6 次...");
    try {
      const result = await api("refresh_wallpapers", force);
      if (!result || !result.wallpapers || !result.wallpapers.length) {
        if (notify) toast(result && result.message ? result.message : "壁纸更新失败，已继续使用本地缓存");
        return;
      }
      state.boot.wallpapers = result.wallpapers;
      const preferredId = force && result.downloaded ? result.current_id : current && current.id;
      const preferredIndex = Math.max(0, state.boot.wallpapers.findIndex(item => item.id === preferredId));
      state.wallpaper = preferredIndex;
      renderWallpaperOptions();
      await setWallpaper(preferredIndex, Boolean(force && result.downloaded));
      if (notify) toast(result.message || (result.downloaded ? "已更新壁纸" : "本地缓存可用"));
    } finally {
      button.disabled = false;
      button.classList.remove("loading");
      button.removeAttribute("aria-busy");
    }
  }

  function resetWallpaperTimer() {
    clearInterval(state.wallpaperTimer);
    if (!state.boot.config.wallpaper_auto) return;
    const seconds = Math.max(15, Number(state.boot.config.wallpaper_interval) || 45);
    state.wallpaperTimer = setInterval(() => setWallpaper(state.wallpaper + 1, true), seconds * 1000);
  }

  function renderNavigation() {
    const main = [
      { view: "dashboard", label: "系统概览", icon: "layout-dashboard" },
      { view: "favorites", label: "我的收藏", icon: "star", count: state.boot.config.favorites.length },
      { view: "recent", label: "最近使用", icon: "history", count: state.boot.config.recent.length },
    ];
    const items = main.map(item => navButton(item.view, item.label, item.icon, item.count)).join("");
    const categories = state.boot.categories.map(item => navButton(`category:${item.id}`, item.label, item.icon, state.boot.tools.filter(tool => tool.category === item.id).length)).join("");
    $("#sidebarNav").innerHTML = `${items}<div class="nav-section-label">${safe(state.boot.platform_label)} 工具</div>${categories}`;
    $("#floatingDock").innerHTML = `<button class="dock-btn" data-view="dashboard" title="系统概览"><i data-lucide="layout-dashboard"></i></button>${state.boot.categories.map(item => `<button class="dock-btn" data-view="category:${safe(item.id)}" title="${safe(item.label)}"><i data-lucide="${safe(item.icon)}"></i></button>`).join("")}`;
    markActiveNav();
    icons();
  }

  function navButton(view, label, icon, count) {
    return `<button class="nav-item" data-view="${safe(view)}"><i data-lucide="${safe(icon)}"></i><span>${safe(label)}</span>${count ? `<b class="nav-count">${count}</b>` : ""}</button>`;
  }

  function markActiveNav() {
    $$('[data-view]', $("#sidebarNav")).forEach(button => button.classList.toggle("active", button.dataset.view === state.view));
    $$('[data-view]', $("#floatingDock")).forEach(button => button.classList.toggle("active", button.dataset.view === state.view));
  }

  function tags(tool) {
    const list = [];
    if (tool.admin) list.push('<span class="tag admin">管理员</span>');
    if (tool.danger) list.push('<span class="tag danger">有风险</span>');
    if (tool.reboot) list.push('<span class="tag reboot">需重启</span>');
    return list.join("");
  }

  function toolCard(tool) {
    const favorite = state.boot.config.favorites.includes(tool.id);
    return `<article class="tool-card" data-tool="${safe(tool.id)}" tabindex="0">
      <span class="tool-icon"><i data-lucide="${safe(tool.icon || "wrench")}"></i></span>
      <div><h3>${safe(tool.name)}</h3><p>${safe(tool.desc)}</p><div class="tag-row">${tags(tool)}</div></div>
      <button class="favorite-btn ${favorite ? "active" : ""}" data-favorite="${safe(tool.id)}" title="${favorite ? "取消收藏" : "收藏"}" aria-label="${favorite ? "取消收藏" : "收藏"}"><i data-lucide="star"></i></button>
    </article>`;
  }

  function sectionHeader(icon, title, count, action = "") {
    return `<div class="section-head"><div class="section-title"><span><i data-lucide="${safe(icon)}"></i></span><h2>${safe(title)}</h2><small>${count} 项</small></div>${action}</div>`;
  }

  function renderDashboard() {
    setPageTitle(`${state.boot.platform_label} 工作台`, "系统概览");
    const favorites = state.boot.config.favorites.map(id => state.boot.tools.find(tool => tool.id === id)).filter(Boolean);
    const recent = state.boot.config.recent.map(id => state.boot.tools.find(tool => tool.id === id)).filter(Boolean);
    const quick = (favorites.length ? favorites : recent.length ? recent : state.boot.tools.filter(tool => !tool.danger)).slice(0, 8);
    $("#content").innerHTML = `
      <section class="section"><div class="stats-grid">
        ${statCard("CPU", "cpu", "cpu", "%")}${statCard("内存", "memory", "memory-stick", "%")}${statCard("系统盘", "disk", "hard-drive", "%")}${statCard("运行时间", "uptime", "clock-3", "")}
      </div></section>
      <section class="section">${sectionHeader("pin", favorites.length ? "我的收藏" : recent.length ? "最近使用" : "常用工具", quick.length, '<button class="text-button" data-view="favorites">查看全部</button>')}<div class="quick-strip">${quick.map(quickTool).join("")}</div></section>
      <section class="section">${sectionHeader("grid-2x2", `${state.boot.platform_label} 工具目录`, state.boot.categories.length)}<div class="category-grid">${state.boot.categories.map(categoryCard).join("")}</div></section>
      <section class="section">${sectionHeader("shield-check", "低风险检查", state.boot.tools.filter(tool => !tool.danger).slice(0, 8).length)}<div class="tool-grid">${state.boot.tools.filter(tool => !tool.danger).slice(0, 8).map(toolCard).join("")}</div></section>`;
    icons();
    refreshSnapshot();
  }

  function statCard(label, key, icon, suffix) {
    return `<article class="stat-card"><div><small>${label}</small><div class="stat-value" id="stat-${key}">--${suffix}</div>${key !== "uptime" ? `<progress id="progress-${key}" max="100" value="0"></progress>` : ""}</div><span class="stat-icon"><i data-lucide="${icon}"></i></span></article>`;
  }

  function quickTool(tool) {
    return `<article class="quick-tool" data-tool="${safe(tool.id)}"><span class="mini-icon"><i data-lucide="${safe(tool.icon)}"></i></span><div><strong>${safe(tool.name)}</strong><small>${safe(category(tool.category).label)}</small></div><button class="run-mini" data-run="${safe(tool.id)}" title="运行" aria-label="运行"><i data-lucide="play"></i></button></article>`;
  }

  function categoryCard(item) {
    const count = state.boot.tools.filter(tool => tool.category === item.id).length;
    return `<button class="category-card" data-view="category:${safe(item.id)}"><span class="category-icon"><i data-lucide="${safe(item.icon)}"></i></span><div><h3>${safe(item.label)}</h3><p>${count} 个 ${safe(state.boot.platform_label)} 专用工具</p></div><i data-lucide="chevron-right"></i></button>`;
  }

  function renderToolList(title, tools, icon = "wrench", eyebrow = state.boot.platform_label) {
    setPageTitle(eyebrow, title);
    if (!tools.length) {
      $("#content").innerHTML = `<div class="empty-state"><i data-lucide="search-x"></i><span>没有匹配的工具</span></div>`;
    } else {
      $("#content").innerHTML = `<section class="section">${sectionHeader(icon, title, tools.length)}<div class="tool-grid">${tools.map(toolCard).join("")}</div></section>`;
    }
    icons();
  }

  function renderCategorySections(tools) {
    setPageTitle(`${state.boot.platform_label} 工具目录`, `“${state.search}”的搜索结果`);
    const html = state.boot.categories.map(item => {
      const matches = tools.filter(tool => tool.category === item.id);
      return matches.length ? `<section class="section">${sectionHeader(item.icon, item.label, matches.length)}<div class="tool-grid">${matches.map(toolCard).join("")}</div></section>` : "";
    }).join("");
    $("#content").innerHTML = html || `<div class="empty-state"><i data-lucide="search-x"></i><span>没有匹配的工具</span></div>`;
    icons();
  }

  function renderCurrent() {
    if (!state.boot) return;
    if (state.search) {
      const query = state.search.toLowerCase();
      const matches = state.boot.tools.filter(tool => `${tool.name} ${tool.desc} ${tool.id} ${category(tool.category).label}`.toLowerCase().includes(query));
      renderCategorySections(matches);
    } else if (state.view === "dashboard") {
      renderDashboard();
    } else if (state.view === "favorites") {
      const tools = state.boot.config.favorites.map(id => state.boot.tools.find(tool => tool.id === id)).filter(Boolean);
      renderToolList("我的收藏", tools, "star", "本地收藏");
    } else if (state.view === "recent") {
      const tools = state.boot.config.recent.map(id => state.boot.tools.find(tool => tool.id === id)).filter(Boolean);
      renderToolList("最近使用", tools, "history", "本地记录");
    } else if (state.view.startsWith("category:")) {
      const id = state.view.split(":")[1];
      const item = category(id);
      renderToolList(item.label, state.boot.tools.filter(tool => tool.category === id), item.icon, `${state.boot.platform_label} 专属`);
    }
    markActiveNav();
  }

  async function refreshSnapshot() {
    if (state.view !== "dashboard" || state.search) return;
    const snapshot = await api("system_snapshot");
    if (!snapshot) return;
    for (const key of ["cpu", "memory", "disk"]) {
      const value = snapshot[key];
      const label = $(`#stat-${key}`);
      const progress = $(`#progress-${key}`);
      if (label) label.textContent = Number.isFinite(value) ? `${value}%` : "未知";
      if (progress) progress.value = Number.isFinite(value) ? value : 0;
    }
    const uptime = $("#stat-uptime");
    if (uptime) uptime.textContent = snapshot.uptime || "未知";
  }

  function selectView(view) {
    state.view = view;
    state.search = "";
    $("#topSearch").value = "";
    $("#sidebarSearch").value = "";
    renderCurrent();
    closeSidebar();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function openTool(id) {
    const tool = state.boot.tools.find(item => item.id === id);
    if (!tool) return;
    state.activeTool = tool;
    $("#modalIcon").innerHTML = `<i data-lucide="${safe(tool.icon)}"></i>`;
    $("#modalCategory").textContent = category(tool.category).label;
    $("#modalTitle").textContent = tool.name;
    $("#modalDesc").textContent = tool.desc;
    $("#modalTags").innerHTML = tags(tool) || '<span class="tag">低风险</span>';
    const favorite = state.boot.config.favorites.includes(tool.id);
    $("#modalFavorite span").textContent = favorite ? "取消收藏" : "收藏";
    $("#toolModal").showModal();
    icons();
  }

  async function toggleFavorite(id) {
    const result = await api("toggle_favorite", id);
    if (!result || !result.ok) return toast("收藏状态更新失败");
    const list = state.boot.config.favorites;
    const active = result.active;
    if (active && !list.includes(id)) list.unshift(id);
    if (!active && list.includes(id)) list.splice(list.indexOf(id), 1);
    renderNavigation();
    renderCurrent();
    if (state.activeTool && state.activeTool.id === id && $("#toolModal").open) $("#modalFavorite span").textContent = active ? "取消收藏" : "收藏";
    toast(active ? "已加入收藏" : "已取消收藏");
  }

  function askConfirm(title, text, proceedText, callback) {
    state.pendingConfirm = callback;
    $("#confirmTitle").textContent = title;
    $("#confirmText").textContent = text;
    $("#confirmProceed").textContent = proceedText;
    $("#confirmModal").showModal();
  }

  async function runTool(id, confirmed = false) {
    $("#toolModal").close();
    const result = await api("run_tool", id, confirmed);
    if (!result) return toast("无法调用本地工具");
    if (result.browser_mode) return toast(result.message);
    if (result.needs_confirmation) return askConfirm("危险操作确认", result.message, "确认运行", () => runTool(id, true));
    if (result.needs_admin) return askConfirm("需要管理员权限", result.message, "请求权限", elevate);
    if (!result.ok) return toast(result.message || "工具未能启动");
    const recent = state.boot.config.recent;
    if (recent.includes(id)) recent.splice(recent.indexOf(id), 1);
    recent.unshift(id);
    state.boot.config.recent = recent.slice(0, 12);
    renderNavigation();
    $("#logDrawer").classList.add("open");
    toast("工具已开始运行");
  }

  async function elevate() {
    const result = await api("elevate");
    toast(result && result.message ? result.message : "已请求权限");
  }

  async function pollActivity() {
    const activity = await api("get_activity", state.logAfter);
    if (!activity) return;
    if (activity.logs && activity.logs.length) {
      state.localLogs.push(...activity.logs);
      state.logAfter = Math.max(state.logAfter, ...activity.logs.map(item => item.seq));
      renderLogs();
      $("#logBadge").textContent = state.localLogs.length;
      $("#logBadge").classList.add("show");
    }
    const running = activity.running;
    $("#taskState").textContent = running ? `运行中 · ${running.name}` : "就绪";
  }

  function renderLogs() {
    $("#logOutput").innerHTML = state.localLogs.length ? state.localLogs.map(item => `<div class="log-line ${safe(item.level)}"><span class="log-time">${safe(item.time)}</span><span class="log-level">${safe(item.level)}</span><span class="log-message">${safe(item.message)}</span></div>`).join("") : '<div class="log-empty">暂无运行记录</div>';
    $("#logOutput").scrollTop = $("#logOutput").scrollHeight;
  }

  function appendMessage(role, text) {
    const wrapper = document.createElement("div");
    wrapper.className = `message ${role}`;
    if (role === "assistant") {
      const icon = document.createElement("span");
      icon.className = "message-icon";
      icon.innerHTML = '<i data-lucide="sparkles"></i>';
      wrapper.append(icon);
    }
    const paragraph = document.createElement("p");
    paragraph.textContent = text;
    wrapper.append(paragraph);
    $("#assistantMessages").append(wrapper);
    $("#assistantMessages").scrollTop = $("#assistantMessages").scrollHeight;
    icons();
    return paragraph;
  }

  async function askAssistant(message) {
    appendMessage("user", message);
    const pending = appendMessage("assistant", "正在分析本地工具目录...");
    $("#assistantSuggestions").innerHTML = "";
    const result = await api("ask_assistant", message);
    pending.textContent = result && result.answer ? result.answer : result && result.message ? result.message : "暂时无法分析该问题";
    $("#assistantMode").textContent = result && result.mode ? result.mode : "离线诊断";
    const suggestions = result && result.suggestions ? result.suggestions : [];
    $("#assistantSuggestions").innerHTML = suggestions.map(tool => `<button class="suggestion-chip" data-tool="${safe(tool.id)}">${safe(tool.name)}</button>`).join("");
    icons();
  }

  function openAssistant() {
    $("#assistantDrawer").classList.add("open");
    $("#drawerBackdrop").classList.add("open");
    setTimeout(() => $("#assistantInput").focus(), 180);
  }
  function closeAssistant() {
    $("#assistantDrawer").classList.remove("open");
    $("#drawerBackdrop").classList.remove("open");
  }
  function openSidebar() { $("#sidebar").classList.add("open"); $("#sidebarBackdrop").classList.add("open"); }
  function closeSidebar() { $("#sidebar").classList.remove("open"); $("#sidebarBackdrop").classList.remove("open"); }

  function openSettings() {
    const cfg = state.boot.config;
    $("#themeSelect").value = cfg.theme;
    applyFontScale(cfg.font_scale);
    $("#wallpaperSelect").value = String(state.wallpaper);
    $("#wallpaperAuto").checked = Boolean(cfg.wallpaper_auto);
    $("#aiProvider").value = cfg.ai.provider || "offline";
    $("#aiEndpoint").value = cfg.ai.endpoint || "";
    $("#aiModel").value = cfg.ai.model || "";
    $("#rememberKey").checked = Boolean(cfg.ai.remember_key);
    $("#aiKey").value = "";
    updateAiFields();
    $("#settingsModal").showModal();
  }

  function updateAiFields() {
    const provider = $("#aiProvider").value;
    $$(".ai-field").forEach(row => row.hidden = provider === "offline");
    $$(".ai-key-field").forEach(row => row.hidden = provider !== "openai");
    if (provider === "ollama" && !$("#aiEndpoint").value.includes("11434")) {
      $("#aiEndpoint").value = "http://127.0.0.1:11434/api/chat";
      $("#aiModel").value = "qwen2.5:3b";
    }
  }

  async function saveSettings(event) {
    event.preventDefault();
    const visual = {
      theme: $("#themeSelect").value,
      font_scale: Number($("#fontScale").value) / 100,
      wallpaper: Number($("#wallpaperSelect").value),
      wallpaper_id: state.boot.wallpapers[Number($("#wallpaperSelect").value)].id,
      wallpaper_auto: $("#wallpaperAuto").checked,
      wallpaper_interval: state.boot.config.wallpaper_interval || 45,
    };
    const aiSettings = {
      provider: $("#aiProvider").value,
      endpoint: $("#aiEndpoint").value.trim(),
      model: $("#aiModel").value.trim(),
      api_key: $("#aiKey").value.trim(),
      remember_key: $("#rememberKey").checked,
    };
    const [visualResult, aiResult] = await Promise.all([api("save_settings", visual), api("set_ai_settings", aiSettings)]);
    if (!visualResult || !visualResult.ok || !aiResult || !aiResult.ok) return toast("设置保存失败");
    state.boot.config = { ...state.boot.config, ...visual, ai: { ...state.boot.config.ai, ...aiSettings, api_key: undefined } };
    applyTheme(visual.theme);
    applyFontScale(visual.font_scale);
    setWallpaper(visual.wallpaper);
    resetWallpaperTimer();
    $("#settingsModal").close();
    toast("设置已保存到本机");
  }

  function updateConnectionStatus() {
    const online = navigator.onLine;
    $("#connectionStatus span:last-child").textContent = online ? "联网增强可用" : "离线核心就绪";
    $("#connectionStatus").title = online ? "所有核心工具仍在本机运行" : "无需网络即可使用核心工具";
  }

  function toast(text) {
    const element = $("#toast");
    element.textContent = text;
    element.classList.add("show");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => element.classList.remove("show"), 2300);
  }

  function bindEvents() {
    document.addEventListener("click", event => {
      const view = event.target.closest("[data-view]");
      if (view) return selectView(view.dataset.view);
      const favorite = event.target.closest("[data-favorite]");
      if (favorite) { event.stopPropagation(); return toggleFavorite(favorite.dataset.favorite); }
      const run = event.target.closest("[data-run]");
      if (run) { event.stopPropagation(); return runTool(run.dataset.run); }
      const tool = event.target.closest("[data-tool]");
      if (tool) return openTool(tool.dataset.tool);
      if (event.target.closest("[data-open-assistant]")) return openAssistant();
      if (event.target.closest("[data-close-assistant]")) return closeAssistant();
      if (event.target.closest("[data-close-modal]")) return $("#toolModal").close();
      if (event.target.closest("[data-close-settings]")) return $("#settingsModal").close();
    });
    $("#menuBtn").addEventListener("click", openSidebar);
    $("#sidebarClose").addEventListener("click", closeSidebar);
    $("#sidebarBackdrop").addEventListener("click", closeSidebar);
    $("#drawerBackdrop").addEventListener("click", closeAssistant);
    $("#themeToggle").addEventListener("click", async () => {
      const theme = document.body.dataset.theme === "dark" ? "light" : "dark";
      applyTheme(theme);
      await api("save_settings", { theme });
    });
    $("#wallpaperNext").addEventListener("click", () => setWallpaper(state.wallpaper + 1, true));
    $("#wallpaperRefresh").addEventListener("click", () => refreshWallpapers(true, true));
    $("#settingsOpen").addEventListener("click", openSettings);
    $("#settingsForm").addEventListener("submit", saveSettings);
    $("#fontScale").addEventListener("input", event => applyFontScale(Number(event.target.value) / 100));
    $("#wallpaperSelect").addEventListener("change", event => setWallpaper(Number(event.target.value)));
    $("#aiProvider").addEventListener("change", updateAiFields);
    $("#openConfig").addEventListener("click", async () => { const result = await api("open_config_folder"); if (!result || !result.ok) toast(result && result.message ? result.message : "无法打开目录"); });
    $("#modalFavorite").addEventListener("click", () => state.activeTool && toggleFavorite(state.activeTool.id));
    $("#modalRun").addEventListener("click", () => state.activeTool && runTool(state.activeTool.id));
    $("#confirmCancel").addEventListener("click", () => { state.pendingConfirm = null; $("#confirmModal").close(); });
    $("#confirmProceed").addEventListener("click", () => { const callback = state.pendingConfirm; state.pendingConfirm = null; $("#confirmModal").close(); if (callback) callback(); });
    $("#logToggle").addEventListener("click", () => $("#logDrawer").classList.toggle("open"));
    $("#logClose").addEventListener("click", () => $("#logDrawer").classList.remove("open"));
    $("#logClear").addEventListener("click", () => { state.localLogs = []; renderLogs(); $("#logBadge").classList.remove("show"); });
    $("#assistantForm").addEventListener("submit", event => { event.preventDefault(); const input = $("#assistantInput"); const message = input.value.trim(); if (!message) return; input.value = ""; askAssistant(message); });
    for (const input of [$("#topSearch"), $("#sidebarSearch")]) {
      input.addEventListener("input", event => {
        state.search = event.target.value.trim();
        $("#topSearch").value = event.target.value;
        $("#sidebarSearch").value = event.target.value;
        renderCurrent();
      });
    }
    document.addEventListener("keydown", event => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); $("#topSearch").focus(); }
      if (event.key === "Escape") { closeSidebar(); closeAssistant(); }
      if (event.key === "Enter" && event.target.classList.contains("tool-card")) openTool(event.target.dataset.tool);
    });
    window.addEventListener("online", updateConnectionStatus);
    window.addEventListener("offline", updateConnectionStatus);
  }

  async function initialize() {
    if (state.initialized) return;
    state.initialized = true;
    state.boot = await api("get_bootstrap");
    if (!state.boot) state.boot = mockBoot;
    if (isBrowserMode()) {
      $("#browserNotice").hidden = false;
      $("#browserPlatform").value = state.boot.platform;
    }
    $("#appName").textContent = state.boot.app_name;
    $("#mobileAppName").textContent = state.boot.app_name;
    $("#platformLabel").textContent = state.boot.platform_label;
    $("#mobilePlatform").textContent = state.boot.platform_label.toUpperCase();
    $("#appVersion").textContent = state.boot.version;
    $("#adminStatus span").textContent = state.boot.is_admin ? "管理员" : "标准权限";
    $("#adminStatus").classList.toggle("admin", state.boot.is_admin);
    applyTheme(state.boot.config.theme);
    applyFontScale(state.boot.config.font_scale);
    const savedWallpaper = state.boot.wallpapers.findIndex(item => item.id === state.boot.config.wallpaper_id);
    state.wallpaper = savedWallpaper >= 0 ? savedWallpaper : Number(state.boot.config.wallpaper) || 0;
    renderWallpaperOptions();
    await setWallpaper(state.wallpaper);
    renderNavigation();
    renderCurrent();
    updateConnectionStatus();
    resetWallpaperTimer();
    setInterval(refreshSnapshot, 10000);
    setInterval(pollActivity, 1000);
    icons();
    if (navigator.onLine && window.pywebview && window.pywebview.api) refreshWallpapers(false, false);
  }

  bindEvents();
  if ($("#browserPlatform")) $("#browserPlatform").addEventListener("change", event => { localStorage.setItem("ops-toolbox-platform", event.target.value); window.location.reload(); });
  document.addEventListener("pywebviewready", initialize, { once: true });
  window.addEventListener("DOMContentLoaded", () => {
    const previewDelay = location.protocol === "http:" || location.protocol === "https:" ? 350 : 3000;
    setTimeout(initialize, previewDelay);
  });
})();
