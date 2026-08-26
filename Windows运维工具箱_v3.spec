# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

project = Path(SPECPATH)
datas = [
    (str(project / 'web' / 'index.html'), 'web'),
    (str(project / 'web' / 'styles.css'), 'web'),
    (str(project / 'web' / 'app.js'), 'web'),
    (str(project / 'web' / 'vendor' / 'lucide.min.js'), 'web/vendor'),
    (str(project / 'web' / 'vendor' / 'LUCIDE_LICENSE.txt'), 'web/vendor'),
    (str(project / 'web' / 'assets' / 'ATTRIBUTION.md'), 'web/assets'),
]
datas += [(str(path), 'web/assets/wallpapers') for path in (project / 'web' / 'assets' / 'wallpapers').glob('*.webp')]

hiddenimports = [
    'modules.app', 'modules.web_app', 'modules.web_bridge', 'modules.wallpaper_cache', 'modules.platform_detect',
    'modules.data', 'modules.data_mac', 'modules.data_linux', 'modules.unix_tools',
    'modules.ui', 'modules.utils', 'modules.network', 'modules.system', 'modules.cleanup',
    'modules.boot', 'modules.optimize', 'modules.info', 'modules.tools', 'modules.diagnose',
] + collect_submodules('webview')

a = Analysis(['运维工具箱.py'], pathex=[str(project)], binaries=[], datas=datas,
             hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=[], noarchive=False, optimize=0)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='Windows运维工具箱_v3',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False,
          disable_windowed_traceback=False, argv_emulation=False, target_arch=None,
          codesign_identity=None, entitlements_file=None)
