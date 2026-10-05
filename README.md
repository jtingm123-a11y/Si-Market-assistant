# Si Market助手

一个运行在本地电脑上的 Streamlit 多市场研究助手，覆盖 A 股、Crypto 和美股行情，并提供技术指标、财务数据和规则化研究结论。

项目不依赖大语言模型，主要面向个人学习、数据整理和投资研究流程管理。所有结果仅供参考，不构成投资建议。

## 主要功能

### 市场观察

- 查看上证、深证、恒生、标普 500、纳斯达克、日经等主要市场
- 查看 BTC、ETH、BNB、XRP、SOL 等主流 Crypto，报价以 USDT 展示
- 使用卡片、涨跌幅图和行情表格观察跨市场表现
- 点击刷新后才请求全球指数和 Crypto 行情
- 显示全球行情最近刷新时间
- 部分市场请求失败时单独提示，不影响其他市场显示

### A 股

- 获取股票基本信息和日线行情
- 支持 AkShare、腾讯财经、新浪财经行情源
- 自动计算 MA5、MA10、MA20、MA60、MACD、KDJ、RSI
- K 线、成交量和 MACD 共用时间轴，可同步缩放和拖动
- 显示收盘价、涨跌幅、成交量和成交额
- 提供技术面、财务面、趋势强度和风险指标评分
- 提供技术分析师、基本面分析师、风险经理和研究主管视角
- 显示北京时间及按常规工作日交易时段估算的开盘状态
- 评分维度使用横向条形图展示

### Crypto

- 查询主流数字资产日线行情
- 查看历史 K 线和成交量
- Crypto 行情统一按 USDT 报价，并按每日 USDT/USD 数据换算
- 支持 1 个月、3 个月、6 个月和 1 年范围
- 手动扫描至少 10 种主流币，显示币种类别、日涨跌和成交量异动依据

### 美股

- 查询 AAPL、MSFT、NVDA、AMZN、GOOGL、META、TSLA 等热门股票
- 支持输入其他美股代码
- 查看历史 K 线和成交量

### 自选观察

- 分别管理 A 股、Crypto 和美股观察标的
- 添加、删除和备注观察标的
- 查看观察池最新行情
- 支持按添加时间、涨跌幅和代码排序
- 支持按市场刷新行情
- 支持从观察池直接进入对应市场研究页
- 股票名称和行情结果使用本地缓存，减少重复请求

### 研究报告

- 为 A 股、Crypto 和美股生成结构化 Markdown 研究报告
- A 股报告包含财务评分；Crypto 和美股报告包含技术指标、趋势与风险观察
- 报告包含基本信息、关键指标、规则化研判和风险提示
- 支持下载报告或保存到 `data/exports`

## 数据可靠性

- 日线行情成功获取后保存到 SQLite 本地数据库
- 新交易日会自动检查行情缓存是否过期
- 行情刷新失败时，已有本地缓存仍可继续使用
- 财务数据默认缓存 24 小时
- 数据页面显示行情来源、数据截止日期和刷新时间
- 数据库启动时自动创建所需数据表

## 项目结构

```text
.
├── app.py                         # Streamlit 应用入口和页面导航
├── pages/                         # 首页、市场观察、个股研究等页面
├── src/
│   ├── analysis/                  # 技术指标、评分和规则分析
│   ├── data_sources/              # 行情、财务、基本信息和全球市场数据源
│   ├── database/                  # SQLite 连接、表结构和数据仓库
│   ├── reports/                   # 研究报告生成
│   ├── services/                 # 行情、评分和股票池业务逻辑
│   └── utils/                    # 格式化等通用工具
├── tests/                         # 自动化测试
├── config/                        # 项目配置
├── data/                          # 本地数据库、缓存和报告导出目录
├── requirements.txt               # Python 依赖
└── run_app.ps1                    # Windows 启动脚本
```

## 安装和启动

要求：Windows、Python 3.10 或更高版本，并确保 Python Launcher（`py`）或 `python` 命令可用。

### 推荐：一键启动

```powershell
cd "$HOME\Desktop\Si Market助手"
.\run_app.ps1
```

首次启动时，脚本会自动创建 `.venv` 并安装 `requirements.txt` 中的依赖；以后启动会复用环境，仅当依赖清单变化时重新安装。请从 VS Code 或 PowerShell 终端运行，这样启动错误会留在终端中，不会像双击窗口那样一闪而过。

如果 Windows 阻止脚本执行，可在 PowerShell 中使用当前进程级执行策略启动：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_app.ps1
```

### 发布给不熟悉 Python 的用户

维护者可在依赖可正常下载的 Windows x64 电脑上执行：

```powershell
.\build_portable.ps1
```

脚本会在发布者电脑上下载便携 Python、安装项目依赖并生成 `dist\A-Stock-Assistant-Windows-x64.zip`。将 ZIP 上传到 GitHub Releases；用户下载完整 ZIP、解压后双击 `run_portable.bat` 即可启动，无需安装 Python 或等待首次 pip 安装。发布包不会包含维护者本机的数据库、股票池、报告或密钥。

打包阶段仍需联网下载 Python 和依赖；运行阶段不需要下载这些依赖，但在线行情与财务数据仍需要网络。发布包适用于 Windows x64。重新发布时上传新的 ZIP；用户应先备份解压目录里的 `data`，不要用旧版数据库覆盖新版用户数据。

### 手动启动

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

如果系统没有 `py` 命令，可将第一行的 `py -3` 替换为 `python`。Streamlit 依赖要求版本为 `>=1.57,<2.0`。在 VS Code 中应启动 Streamlit 应用，不要使用“运行 Python 文件”直接运行页面脚本。

## 使用说明

1. 启动应用并打开“个股研究”。
2. 输入六位股票代码，例如 `600519` 或 `000001`。
3. 点击“开始研究”获取行情和分析结果。
4. 在“我的股票池”中保存需要长期跟踪的股票。
5. 在“研究报告”中生成和导出 Markdown 报告。

首次查询新股票需要联网。数据源可能存在延迟、限流或临时不可用的情况。

## 测试

在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

## 数据和敏感文件

以下内容只保存在本地，不应提交到 GitHub：

- `data/stock_assistant.db`
- `data/exports/`
- `.venv/`
- `.env`
- `.streamlit/secrets.toml`
- Python 缓存和测试缓存

项目已通过 `.gitignore` 忽略常见本地数据和敏感配置。
从 GitHub 下载代码后，本地数据库和个人数据不会自动包含在下载内容中；若需迁移，请先关闭应用，再手动复制旧项目的 `data/stock_assistant.db` 到新项目的 `data` 目录。不要把个人数据库强制提交到公开仓库。

### 备份项目

在项目根目录的 PowerShell 中运行以下命令，会在项目同级目录创建带时间戳的备份，保留 `data` 和本地配置，同时跳过 Git 元数据、虚拟环境、缓存及可重新生成的打包文件：

```powershell
$backupPath = "..\Si Market助手-backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
robocopy . $backupPath /E /XD .git .venv __pycache__ .pytest_cache build dist
if ($LASTEXITCODE -ge 8) { throw "备份失败，robocopy 退出代码：$LASTEXITCODE" }
```

备份中可能包含 `.env`、密钥或个人数据库，请仅保存在可信位置，不要上传到公开仓库。

## 免责声明

本项目使用公开数据和固定规则生成研究辅助信息，不保证数据完整性、及时性或准确性。技术指标和评分具有滞后性，不能作为买卖依据。使用者应独立核验公司公告、财务报告、估值、市场环境和自身风险承受能力。
