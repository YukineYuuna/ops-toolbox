# Visual asset source

The application obtains its wallpaper output from the user-selected Sakura random image API and keeps validated WebP copies for offline use.

## Wallpaper API

- Provider: Sakura random image API (`api.r10086.com`)
- Endpoint: `https://api.r10086.com/樱道随机图片api接口.php`
- Bundled file: `wallpapers/api-offline-b51a492d53e703b7.webp`
- Downloaded: 2026-08-27
- Processing: validated, center-fitted to 1920×1080, and encoded as WebP.

The API provider controls the underlying image catalog. Before publicly redistributing an installer containing cached wallpaper, confirm that the selected image's usage terms permit redistribution.
