# 每日 AI 行业简报 · 网页版

由 WorkBuddy 自动生成的每日 AI 行业简报静态站点，部署到 GitHub Pages 后可通过固定网址在手机/电脑浏览器查看，并保留全部历史往期。

## 目录结构

```
ai-daily-site/
├── index.html          # 固定入口：最新一期 + 往期列表
├── 2026-07-19.html     # 每日独立页（永久保留，不覆盖）
├── 2026-07-20.html
├── ...
├── assets/
│   └── style.css       # 移动端友好样式
├── generate.py         # md → 网页 生成器
└── README.md
```

## 每日自动更新流程（由 WorkBuddy 自动化任务执行）

1. 检索过去 24 小时 AI 新闻，生成 `automation/ai-daily/YYYY-MM-DD-ai-daily.md`
2. 运行 `generate.py <md路径> <站点目录>`：
   - 产出当天独立页 `YYYY-MM-DD.html`
   - 重新生成 `index.html`（最新一期 + 扫描全部往期页自动累积列表）
3. `git add -A && git commit && git push` 推送到本仓库
4. GitHub Pages 自动更新，固定网址即显示当天内容

## 本地手动生成

```bash
python3 generate.py /path/to/YYYY-MM-DD-ai-daily.md /path/to/ai-daily-site
```

## 启用 GitHub Pages

仓库 Settings → Pages → Source 选择 `main` 分支根目录 → Save。
约 1 分钟后访问 `https://<用户名>.github.io/<仓库名>/`。
