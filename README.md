# Si Market助手

基于 Streamlit 的本地多市场研究工具，覆盖 A 股、Crypto 和美股，提供行情查看、技术指标、规则化分析、自选管理及研究报告。项目面向学习和研究，不构成投资建议。

## 功能

- **市场总览**：查看全球主要指数和主流 Crypto；点击“刷新数据”获取最新市场总览。
- **资讯**：按专题筛选公开新闻和政策资讯，支持来源筛选、关键词搜索及原文链接。
- **A 股**：查询日线、财务和技术指标；扫描新浪财经公开榜单中的换手率活跃股和成交额靠前股。
- **美股与 Crypto**：查询日线行情；图表可选择 MA5、MA10、MA20、MA60，并显示成交量和 MACD；支持各自的热门/异动扫描。
- **自选**：管理 A 股、Crypto 和美股标的，查看及刷新行情。
- **基础分析报告**：生成、下载、查看和对比报告；支持多选历史报告并在确认后删除。

行情来自公开数据源，可能延迟、限流或暂时不可用。扫描和分析结果仅供研究参考。

## Windows 启动

要求 Windows 和 Python 3.10 或更高版本。推荐在项目根目录用 PowerShell 启动：

```powershell
.\run_app.ps1
```

脚本会自动建立 `.venv` 并安装依赖。若执行策略阻止运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_app.ps1
```

也可手动创建环境并启动：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Windows 便携版

在 Windows x64、可下载 Python 和依赖的环境中构建：

```powershell
.\build_portable.ps1
```

构建完成后，将 `dist\A-Stock-Assistant-Windows-x64.zip` 上传到 GitHub Releases。用户解压后运行 `run_portable.bat`。便携版不包含构建者的数据库或个人配置；在线行情仍需网络。

发布新版本前，先提交并推送代码，再创建对应标签。例如发布 `v1.1.0`：

```powershell
git add -A
git status
git commit -m "Release Si Market助手 v1.1.0"
git push origin main
git tag -a v1.1.0 -m "Si Market助手 v1.1.0"
git push origin v1.1.0
.\build_portable.ps1
```

在 GitHub Releases 创建同名版本并上传生成的 ZIP。ZIP 是发布附件，不要提交到源代码仓库。

## 测试

在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

## 本地数据与备份

SQLite 数据库、导出报告和密钥保存在本地。不要将个人数据库、`.env` 或 `.streamlit/secrets.toml` 提交到公开仓库。

在项目根目录运行以下命令，可在项目同级目录创建带时间戳的备份：

```powershell
$backupPath = "..\Si Market助手-backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
robocopy . $backupPath /E /XD .git .venv __pycache__ .pytest_cache build dist
if ($LASTEXITCODE -ge 8) { throw "备份失败，robocopy 退出代码：$LASTEXITCODE" }
```

备份包含本地数据和配置，请存放在可信位置，不要上传到公开仓库。迁移数据库前请关闭应用，并单独复制 `data\stock_assistant.db`。

## 项目结构

```text
app.py             Streamlit 应用入口
pages/             市场总览及研究页面
src/               行情数据、分析、数据库和业务服务
config/            应用配置
tests/             自动化测试
data/              本地数据库及导出目录
requirements.txt   Python 依赖
run_app.ps1        Windows 启动脚本
build_portable.ps1 Windows 便携版构建脚本
```
