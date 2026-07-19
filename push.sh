#!/bin/bash
# 一键把当日简报推送到 GitHub Pages
# 用法：bash push.sh
set -e

SITE_DIR="/Users/caicai/WorkBuddy/每日 AI 行业简报/ai-daily-site"
cd "$SITE_DIR"

DATE=$(date +%Y-%m-%d)
git add -A
# 若没有改动则跳过提交
if git diff --cached --quiet; then
  echo "[push.sh] 没有需要提交的改动，跳过。"
  exit 0
fi
git commit -m "daily: ${DATE} AI 简报"
git push origin main
echo "[push.sh] 已推送 ${DATE}，GitHub Pages 将在 1-2 分钟内更新。"
