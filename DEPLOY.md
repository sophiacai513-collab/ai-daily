# 部署到 GitHub Pages 指南

把每日 AI 简报变成一个**固定网址**，手机书签后每天打开都是最新一期 + 全部历史。

> 说明：WorkBuddy 的沙箱环境禁止写入 `~/.ssh` 且无法替你登录 GitHub，
> 因此「生成密钥 / 登录 GitHub / 建仓库」这几步需要你在**自己电脑的终端**里完成。
> 下面的命令直接复制粘贴运行即可。

---

## 第一步：生成 SSH 密钥（只需一次）

打开你 Mac 的「终端」App（Launchpad 搜“终端”），粘贴运行：

```bash
ssh-keygen -t ed25519 -C "caicai-ai-daily"
# 出现提示一律直接回车（不设置密码短语，便于每天自动推送）
cat ~/.ssh/id_ed25519.pub
```

最后一行会输出一整段以 `ssh-ed25519` 开头的文本，**全选复制**备用。

## 第二步：把公钥加到 GitHub

1. 浏览器打开 https://github.com → 登录
2. 右上角头像 → **Settings** → 左侧 **SSH and GPG keys**
3. 点 **New SSH key** → Title 填 `ai-daily` → 把刚才复制的公钥粘贴进 Key 框 → **Add SSH key**

## 第三步：建一个空仓库

1. 右上角 **+** → **New repository**
2. Repository name 填 `ai-daily`
3. 选 **Public**
4. **不要**勾选任何初始化选项（README/.gitignore 都别勾）→ **Create repository**

## 第四步：连接并推送（在终端运行）

把下面 `你的用户名` 换成你的 GitHub 用户名，然后整段粘贴运行：

```bash
cd "/Users/caicai/WorkBuddy/每日 AI 行业简报/ai-daily-site"
git remote add origin git@github.com:你的用户名/ai-daily.git
git push -u origin main
```

看到进度条推完即成功。

## 第五步：开启 GitHub Pages

1. 进入刚建的 `ai-daily` 仓库 → **Settings** → 左侧 **Pages**
2. Branch 选 **main** → 点 **Save**
3. 等 1–2 分钟，你的网址就是：

```
https://你的用户名.github.io/ai-daily/
```

把这个网址**加到手机书签**，通勤时一点即开。

---

## 之后每天

自动化任务（每天 08:00）会自动：检索新闻 → 生成 md → 跑 `generate.py` 出网页 →
`git push` 到该仓库 → GitHub Pages 刷新。你**无需再做任何事**，书签永远是最新。

### 手动补推（可选）
若某天想手动更新，在终端运行站点目录下的脚本：

```bash
cd "/Users/caicai/WorkBuddy/每日 AI 行业简报/ai-daily-site"
bash push.sh
```
