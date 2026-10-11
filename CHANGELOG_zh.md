# 更新日志

本项目所有显著变更均记录于此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/)。

[English](CHANGELOG.md) | 简体中文

## [1.0.1] - 2026-10-10

### 新增

- 支持 Python 3.15：classifiers 覆盖 3.10–3.15，CI 矩阵测试全部六个版本（3.13/3.14 此前
  已声明但从未实测）。
- Release 驱动发布：tag 推送时 `prepare-release.yml` 经新增的 `tools/extract_changelog.py`
  从 `CHANGELOG.md` / `CHANGELOG_zh.md` 抽取该版本段落，自动创建双语草稿 GitHub Release；
  点击 Publish 后 `release.yml` 才构建并上传 PyPI——两个 workflow 均校验 tag 与 `__version__` 一致。
- 文档化 Filter 形态指标口径（AC 值、各彩种三区分界、012 路、质数、连号对数），并以单元测试
  锁定精确语义（`tests/test_predict.py`）。
- `predict.py` 中数学较重的部分补充行内注释（和值带 MA ± k·σ、卡方期望频次、AC 值、遗漏分、
  Efraimidis–Spirakis 加权采样）。

### 变更

- 双语 README 重构：新增提纲目录；文档站链接提升至页首（居中链接 + Docs 徽章）；
  Python 要求表述为 3.10 – 3.15。
- 两份 README 与文档站首页的代码块统一改为 black 风格竖排调用（≤ 79 列），窄屏不再出现
  断行错位。
- `RELEASE.md` 按 Release 驱动流程重写并附逐步发布教程；发布说明由手工粘贴改为自动生成。
- README 精简重构：目录由 16 项减至 7 项；彩种 / 策略 / 数据来源合并为一节；快速上手改为
  单个走缓存的完整流程（文档站首页同步，并补上中奖校验一步）；API 一览、本地缓存、开奖详情、
  浮动奖配置与统计小节移除——均由文档站完整承载。
- README 开场去重：删除导语段（标语与"项目特点"四条各讲一遍即可）；四条特点与文档站首页卡片
  均按流水线重排（数据 → 数学 → 策略（核心）→ 流水线）；首页中插的规则核实段落折入
  "只采官方数据"卡片并保留 Games & Rules 链接，快速上手补齐与 README 相同的引导句。
- 性能优化：`load_number_statistics` 与策略构造器（frequency / tail / omission / markov /
  markov2）改为一次性解析出现矩阵 + numpy 向量化计算——全历史统计提速约 250–380 倍
  （ssq 3000 期：1.2s → 0.015s；kl8 8000 期：5.8s → 0.04s），结果经纯 Python 参考实现
  对拍测试验证完全一致；backtest 预解析真实开奖并按策略复用解析结果；`numpy` 成为显式
  依赖（兼容 pandas >= 2.3.3 与 3.x）。
- 按 PEP 561 发布 `py.typed` 标记（随 wheel package-data 分发），下游 `mypy` 用户可直接
  获得内联类型；新增 PR 模板；pre-commit 升级至 ruff v0.17.0（ruff + ruff-format）并挂载
  按项目依赖集钉版的 mypy hook。
- 历史开奖 / 随机选号 / 策略选号返回的 DataFrame 新增 `lottery_zh_name` 列（接口展示名，
  如 '双色球'），紧跟 `lottery_name`（其值保持为游戏代码）；入口管道改为按列名映射原始
  接口字段，不再依赖位置对齐。旧缓存 CSV 自动迁移（展示名映射为代码、缺失列自动补齐）。
- 体彩系彩种（dlt / pls / plw / qxc）缓存命中不再全量重抓：体彩接口无日期窗口查询，
  增量刷新改为从最新页翻页、与缓存期号出现交集即停（通常仅第 1 页；翻完全部页数则
  等价全量刷新并由去重兜底），且与全量抓取共用同款 rich 进度条——重叠即停时总数收缩
  为实抓页数，info 字段报告真实行数；探测页数的 warmup 现显式返回总页数。实测效果：
  缓存已是最新时，dlt 刷新从全量爬取约 15s 降为即时。
- `lottery_name` 在入口层归一为游戏代码（`ssq`/`dlt`/...）：原始接口携带的是展示名
  （'双色球'/'超级大乐透'），而库内其余部分与文档均以代码为准，此前两者不一致。
- 缓存已覆盖到今天（或接口返回了未来日期行）时，增量刷新不再崩溃：此前推导出的
  `begin_date` 落在今天之后而被 `check_params` 拒绝。现缓存层在该情况下跳过网络抓取、
  直接返回缓存内容。
- `backtest` 明细新增 `lottery_name` 列；`backtest_summary` 新增四个比率列：
  `avg_red_hit_rate` / `avg_blue_hit_rate`（策略平均命中 ÷ 每期开出球数——单注捕获了
  当期开出球的几分之几）与 `random_red_hit_rate` / `random_blue_hit_rate`（`random`
  基线的实测捕获率，逐行重复显示作对照；结果集不含 random 时为 NaN）。理论捕获率为
  `R ÷ N`、`B ÷ N_blue`（如双色球红球 6 ÷ 33 ≈ 18%），策略与基线都应贴近该值；
  `backtest_summary` 相应按 `lottery_name + method` 分组。
- 进度条重建于 rich（取代 tqdm 并将其从依赖中移除）：品牌蓝→青真渐变进度条（逐格插值，
  边界用 pip 式半格过渡）、实时日期区间/行数信息、东亚字符宽度正确、stderr 输出、stderr
  非 TTY 时自动静默、完成后进度行保留（pip 式）。

### 修复

- `if_cached=True` 在所有真实路径上都会触发 `RecursionError`（缓存为空的首次拉取、增量
  刷新、明细透传）：该开关被原样回传给 `load_history_data`，导致 data 层与 cache 层互相
  分发直至爆栈。现由缓存层单点消费该开关；并新增回归测试驱动真实的
  `load_history_data → cache → 网络` 分发链路（mock 网络层而非缓存层——旧测法正是因此
  掩盖了此 bug）。
- 官方福彩接口返回的开奖日期带星期后缀（`2026-10-08(四)`），原样进入公共 DataFrame 与
  缓存 CSV，并使增量刷新抛出 `ValueError: Invalid isoformat string`。现于入口层将日期
  规整为 ISO 前缀，且缓存增量解析兼容已写入后缀的旧 CSV（无需手动清理缓存）。
- 增量刷新穿过"无开奖窗口"时抛出 `KeyError: 'code'`：某些日期窗口合法地没有开奖
  （双色球每周三期），空响应被解析成无列名的空表。现空响应在福彩与体彩两条路径上都
  保留预期列名。
- README 的 Python 要求写为 3.9+，与包实际要求 ≥ 3.10 不符。
- 中文文档中 `deviation` 策略描述括号全半角混用（（实际-期望)² → （实际 − 期望）²）。
- `filter` 策略文档注明 `zone_ratio` 与 `mod3_range` 为精确匹配（`mod3_range` 名称易误读为区间）。

## [1.0.0] - 2026-10-03

### 新增

- 全部 8 个彩种（`ssq`、`qlc`、`kl8`、`3d`、`dlt`、`pls`、`plw`、`qxc`）的历史开奖：来自官方接口
  （`cwl.gov.cn` / `lottery.gov.cn`），带重试与指数退避，统一输出为 tidy DataFrame（`data.py`）。
- 本地 CSV 缓存与增量更新：`load_history_data(if_cached=True, cache_dir=...)`（`cache.py`）。
- 全部 8 个彩种的中奖概率、期望与返奖率（`odds.py`）：以现行官方规则做精确组合数学（`math.comb`）
  计算——奖级、中奖条件与固定奖金仅对照 cwl.gov.cn / lottery.gov.cn 核实，规则来源 URL 收录于
  `config.py`。
- 超级大乐透追加投注（3 元/注，浮动奖按 80% 兑付）与复式投注的注数、成本与整票期望，推导过程以
  LaTeX 公式文档化（`odds.py`）。
- 中奖校验：对指定开奖或最新一期开奖返回命中详情、奖级与奖金（`check.py`）。
- 号码统计：红蓝两池每个号码的频率、当前/最大/平均遗漏（`analysis.py`）。
- 策略选号（`predict.py`）：`random` 基线、冷热号（别名 `hot` / `cold`）、遗漏回补（别名 `chase`）、
  卡方偏离（别名 `chisq`）、重号/邻号、和值均线通道、尾数、一阶/二阶马尔可夫、可组合形态缩水
  （和值 / 奇偶 / 质合 / 三区比 / 012 路 / AC 值 / 连号 / 杀号）与多策略集成投票——仅用于统计观察
  与娱乐。策略为纯注入设计（构造器无网络 IO）；`history=` 可完全离线使用。
- 滚动窗口回测：将所有策略与 `random` 基线对比（`backtest.py`）。
- 开奖详情（`draws.py`）：每期销售额与奖池、各奖级中奖注数与单注奖金（含大乐透追加档）、一等奖
  省级分布——三张 tidy 表并支持增量缓存。
- CLI `lotterycn`，子命令 `odds / expect / stats / predict / check / detail / prizes / provinces / backtest`。
- 基于 hypothesis 的属性测试（概率/期望不变量）、覆盖率门槛（`fail_under = 80`）、CI 中的构建产物
  检查、非阻塞 pip-audit 扫描与 Dependabot 配置。
- 双语文档守门 `tools/check_docs_sync.py`——en/zh 页面配对、英文页禁中文、定位词一致、禁内部开奖
  API 域名——接入 CI 作为 test job 的第一步。
- 自托管 MathJax 3.2.2（`docs/assets/mathjax/`：`tex-chtml.js` 组件与 woff-v2 字体）配最小化
  `mathjax.js` 配置，公式在离线环境与公共 CDN 不可达的网络下均可正常渲染。

### 变更

- 重构：`Tse` / `LotteryError` 收拢进 `utils.py`、相对导入、requests 带重试与指数退避、默认超时。
- 打包：元数据迁移至 `pyproject.toml`（`[project]` 表、SPDX 许可证、动态版本、console script）；
  移除 `setup.py`、`setup.cfg`、`MANIFEST`、`MANIFEST.in` 与 `requirements.txt`。
- 测试：`tests/` 下的 pytest 套件，离线/联网分层并带真实断言；移除旧 `lotterycn/test.py`。
- CI：GitHub Actions 矩阵对齐 `requires-python`（3.10–3.12），含 ruff、mypy 与离线 pytest 覆盖率；
  tag 触发的 PyPI 发布工作流；GitHub Pages 部署工作流。
- 项目叙事围绕四大支柱重排，**选号策略与预测回测**为核心卖点：README（中英）导语与项目特点、
  首页卡片，两份 README 均附完整策略表与回测示例；标语统一为 "enjoyable analysis" / 有趣好玩。
- 英文文档页全部为英文（API 页导语、策略术语、games 表链接文字）；中文 README 导语不再混排
  英文句子。
- 内部开奖 API 域名从所有文档与 docstring 中移除；文档仅引用两个官方网站（`cwl.gov.cn`、
  `lottery.gov.cn`）。
- `LotteryError` 在全包范围内附带描述性消息；源码经 `ruff format` 全量格式化。
- 全包 docstring 补全：所有公开函数补齐参数、返回与列结构说明（`backtest`、`backtest_summary`、
  cache / draws / data 辅助方法、12 个策略 `predict` 实现、odds 辅助函数与 utils）；`methods`
  类型标注为 `tuple[str, ...]`、`argv` 为 `list[str] | None`。
- 文档站：中文首页与英文首页完全对齐——hero（logo / 标语 / CTA 按钮）、grid cards 与稳定的
  `#quickstart` 锚点；视觉 pass：双配色方案 teal 强调色、hero 渐变底、2×2 卡片网格配浅蓝绿底色
  与 hover 高亮、呼应 logo 的红紫渐变页脚、策略卡的 `chart-line` 图标。
- MathJax 由公共 CDN 迁移为自托管资源；文档站重建并在无头浏览器中逐条验证公式（中英）。

### 修复

- `:material-show-chart:` 静默回退为原文（不在内置图标集内）→ 改用 `material/chart-line`。
- 文档站全站 LaTeX 公式不渲染（CDN 不可达、`tex-mml-chtml` 组件产出空容器、MathJax 配置过严）
  ——已在无头浏览器对中英两语截图确认修复。
- `README_zh.md`：重写混排英文的导语；补齐快速上手输出示例。

### 文档

- README 以英文重写并附 `README_zh.md`；新增 CONTRIBUTING、CODE_OF_CONDUCT、SECURITY 与
  数据纠错 issue 模板。
- 新增 `RELEASE.md`：面向维护者的发布指南（tag 驱动的 Trusted Publisher 流程）。
- 文档站以 mkdocs-material + mkdocstrings 重建并部署至 GitHub Pages，经 mkdocs-static-i18n 实现
  完全双语（English / 简体中文）与语言切换器；9 个模块的 API 参考自源码生成。
- 双语 docstring（英文正文 + 中文说明 admonition）在四个核心 API 试点：`load_history_data`、
  `load_prize_odds`、`load_check_result`、`load_predict_numbers`。
- 站点排版借鉴 fastapi / pydantic / polars 文档实践：自托管阿里巴巴普惠体 webfont（附 Apache 2.0
  许可证，`font-display: swap`）、Monaco 优先斜体代码风格、docstring 公式的 MathJax 渲染，以及
  间距/排版规整。
- 构建钩子（`hooks.py`）：折叠生成 HTML 中的冗余空行（保护 `<pre>` 块），并把 `site_url` 绝对链接
  按页面深度重写为相对路径，使语言切换器在本地 IDE 预览、离线页面与 GitHub Pages 项目路径下均
  可用（此前 404）。
