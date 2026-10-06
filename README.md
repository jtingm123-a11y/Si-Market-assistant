# Si Market助手

Si Market助手是使用 SI 编程开发的辅助投资研究工具，目前处于初级、持续开发阶段。现在可以查看市场行情和资讯、管理自选股票、生成基础研究报告。Si智能功能还在开发准备中，后续计划接入 SI 模型能力，并持续完善现有页面。

网页和手机均可使用；品牌区包含动态 Si 核心视觉。

> 行情和分析来自公开数据，仅供学习和研究参考，不构成投资建议。

## 怎么使用

### 下载便携版

1. 下载并解压 GitHub Releases 中的 Windows ZIP。
2. 双击 `SiMarketAssistant.exe`。
3. 浏览器打开后即可使用。退出时关闭启动窗口。

便携版不需要另外安装 Python。EXE 启动器需要与 ZIP 中的 `runtime` 文件夹和程序文件放在一起，不能单独从 ZIP 内运行。查看在线行情和资讯需要联网。

开发时可在 PowerShell 运行 `.\run_app.ps1`；需要 EXE 启动器时，在项目目录运行 `.\build_launcher.ps1`，生成的 `SiMarketAssistant.exe` 会使用项目 `.venv` 或便携版 `runtime`。

### 从源码启动

Windows 上安装 Python 3.10 或更高版本，在项目文件夹打开 PowerShell，运行：

```powershell
.\run_app.ps1
```

首次启动会自动准备运行环境和依赖。

## 页面功能

- **Market**：点击“刷新数据”，查看最新市场总览。
- **资讯**：浏览市场资讯，可按专题、来源或关键词筛选。
- **资讯刷新**：打开资讯页后点击“刷新资讯”才会获取数据；更换专题或筛选不会重新请求新闻。
- **A股 / 美股 / Crypto**：查询行情和走势；A股、美股页面还可扫描热门与异动标的。
- **自选**：查看和管理保存的股票。
- **基础分析**：生成研究报告，也可以查看、对比或删除历史报告。
- **Si智能**：展示后续开发方向，智能分析功能目前尚未开放。

## 个人数据备份

自选和历史报告保存在应用目录的 `data` 文件夹。升级前先关闭应用，再复制这整个文件夹；使用新版时保留原有 `data` 文件夹，不要覆盖或删除。

## 发布新版本

下面以 `v1.2.0` 为例。在项目根目录的 PowerShell 中执行。提交前先检查 `git status`，确认只包含准备发布的改动：

```powershell
git add -A
git status
git commit -m "Release Si Market助手 v1.2.0"
git push origin main
git tag -a v1.2.0 -m "Si Market助手 v1.2.0"
git push origin v1.2.0
.\build_portable.ps1
```

构建完成后，将 `dist\Si-Market-Assistant-Windows-x64.zip` 上传到 GitHub Releases 的 `v1.2.0` 版本。解压后运行 `SiMarketAssistant.exe`；EXE 是 ZIP 内的启动器，不能脱离同目录运行环境单独使用。ZIP 是发布附件，不要提交到源代码仓库。

## 运行测试

在项目根目录运行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```
