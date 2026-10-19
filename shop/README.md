# shop.tathr.com

- `选品对比.md`：卖什么的分析和结论（数字产品「概念显影 · 图解卡」）。
- `concept-pack/`：图解卡第一辑。
  - `build.py` + `render.js`：生成 PDF 和预览图（`python3 build.py && node render.js`，需要 segno 和 playwright）。
  - `dist/`：成品 PDF 和商品图。
  - `product/`：商品文案、免费试读、预览模式插件（暂不收款）、主站加入口脚本。
  - `HANDOFF.md`：服务器上线步骤。
