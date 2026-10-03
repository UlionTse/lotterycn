# 更新日志

本项目所有显著变更均记录于此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/)。

[English](CHANGELOG.md) | 简体中文

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
