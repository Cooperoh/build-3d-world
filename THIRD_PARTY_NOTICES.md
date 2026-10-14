# 来源与许可说明

## Rokehan 应用代码

- 作者：MIYADAIKU / おやすみゲーム開発部（Oyasumi Game Dev）。
- 作品：Rokehan / Location Scout / 随处勘景 / どこでもロケハン。
- 来源：<https://tools.oyasumi-gamedev.com/rokehan/>。
- 作者说明：<https://oyasumi-gamedev.com/tools/rokehan/>。
- 留存日期：2026-10-14。
- 对应文件：`app/index.html`。其中包含 HTML、CSS、JavaScript 和 GLSL。

本仓库保存网页向浏览器公开提供的运行文件，用于个人留存和研究。尚未确认原作者为其自有程序发布的开源许可证；本仓库不据此授予再分发许可，也不将其重新许可为 MIT。发布或再分发作者自有代码前，应核实相应授权。

## Three.js 与 OrbitControls

`app/lib/three_hg.js` 来自原网页，是 Three.js r170 与 OrbitControls 的脚本包装版本。文件头标注 Copyright 2010–2024 Three.js Authors，采用 MIT 许可证。保留完整许可文本于 [LICENSE_three.txt](app/lib/LICENSE_three.txt)。

## 地图与高程数据

本仓库不预置地图、高程或搜索数据。运行时取得的数据应遵循各自的许可和服务要求：

- OpenStreetMap：© OpenStreetMap contributors，ODbL，<https://www.openstreetmap.org/copyright>。
- OpenFreeMap / OpenMapTiles：按实际使用保留 OpenFreeMap 与 © OpenMapTiles 等出处，<https://openfreemap.org/>、<https://www.openmaptiles.org/>。
- Terrain Tiles：<https://registry.opendata.aws/terrain-tiles/>。不同地区的底层高程数据来源及要求可能不同。
- 日本国土地理院：<https://maps.gsi.go.jp/development/ichiran.html>。
- Nominatim：遵循其公开服务使用政策，<https://operations.osmfoundation.org/policies/nominatim/>。

原网页的图片和模型导出会写入相关出处；研究和导出时应保留这些说明。

## 本仓库新增内容

`server.py`、`local-cache.js`、启动入口、提取脚本及仓库文档是本地留存和研究整理层。它们不改变原作者核心实现的归属，也不扩大对原作者代码的授权。
