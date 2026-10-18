# 更新日志

本项目所有显著变更均记录于此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/spec/v2.0.0.html)。

[English](CHANGELOG.md) | 简体中文

## [1.0.1] - 2026-10-10

### 亮点（Highlights）

- 核心统计与策略向量化——全历史统计提速 250–380 倍。
- 体彩缓存命中增量刷新（dlt 刷新从约 15 秒降为即时）。
- 进度条重建于 rich（品牌渐变，取代 tqdm）。
- 新增 `lottery_zh_name` 列；`lottery_name` 归一为游戏代码。
- Release 驱动发布：双语草稿 Release + tag/版本守卫。

### 破坏性变更（Breaking Changes）

- `lottery_name` 现为游戏代码（`ssq`/`dlt`），不再是中文展示名。
- `backtest` 明细新增 `lottery_name` 列；`backtest_summary` 结构重排
  （比率列更名，按 `lottery_name + method` 分组）。
- 依赖：移除 `tqdm`；新增 `rich>=15.0.0` 与 `numpy>=1.26.4`。

### 变更（Changes）

- 支持 Python 3.15（classifiers + CI 矩阵 3.10–3.15）。
- 发布工具链：`prepare-release.yml` / `release.yml` / `tools/extract_changelog.py`；
  RELEASE.md 重写；CI 的 ruff/mypy 钉版至 pre-commit 一致版本。
- PEP 561 `py.typed`；pre-commit（ruff v0.17.0 + mypy v2.4.0）；PR 模板；
  非联网用例离线守卫。
- README 精简与去重；文档站首页重排；新增 API Reference 索引页；
  quickstart 示例使用 `if_cached=True` / `sleep_seconds=0.1`。
- 语言统计不再计入文档站构建产物 `site/**` 与自托管 MathJax（`.gitattributes` 的
  `linguist-documentation` / `linguist-vendored` 标记）；`site/` 副本仍保留在仓库中
  供离线预览，其本地变化今后不再提交。
- 安全与质量门禁：依赖审计移出 PR 流程，改为每周定时 `security.yml`（阻塞式告警）；
  覆盖率门槛 80 → 89（当前实测约 90%）。

### 修复（Fixes）

- `if_cached=True` 不再无限递归（开关由缓存层单点消费）。
- 福彩日期的星期后缀（`2026-10-08(四)`）在入口规整为 ISO；兼容旧缓存。
- 空开奖窗口不再触发 `KeyError: 'code'`。
- 缓存已覆盖到今天时，增量刷新跳过网络抓取。
- README 的 Python 要求修正（3.9+ → 3.10–3.15）；`deviation` 括号修正；
  `mod3_range` 注明为精确匹配。

### 备注（Notes）

- 旧缓存 CSV 自动迁移（展示名 → 代码、`lottery_zh_name` 补齐），无需手动清理。
- 仅供娱乐：所有策略与 `random` 基线期望完全相同（可用 `lotterycn.backtest` 验证）。

## [1.0.0] - 2026-10-03

### 亮点（Highlights）

- 全部 8 个彩种的官方历史开奖（`cwl.gov.cn` / `lottery.gov.cn`），带本地缓存与增量更新。
- 精确组合数学的中奖概率、期望与返奖率，及中奖校验。
- 11 个选号策略与对照 `random` 基线的滚动回测。
- 双语文档站与 `lotterycn` 命令行工具。

### 破坏性变更（Breaking Changes）

- 相对 0.0.4 的全面重写：包结构、公开函数与输出 schema 全部更替——
  0.0.4 代码需迁移至新入口。

### 变更（Changes）

- 打包迁移至 `pyproject.toml`（动态版本、console script）；测试迁至 `tests/`
  并区分离线/联网；GitHub Actions CI 矩阵；内部开奖 API 域名从文档中移除。

### 修复（Fixes）

- `material/chart-line` 图标回退；文档站 MathJax 渲染（自托管资源）；
  `README_zh.md` 导语重写。

### 备注（Notes）

- 数据来源仅限官方渠道——奖级规则与开奖数据只对照 `cwl.gov.cn` /
  `lottery.gov.cn` 核实，绝不使用第三方站点。
- 策略仅供统计观察与娱乐，不构成预测。

## [0.0.4] - 2022-11-18

### 变更（Changes）

- 统一输出 schema：全部 8 个彩种（含 kl8）返回相同五列
  （`lottery_name` … `lottery_blue`）。

## [0.0.3] - 2022-11-10

### 亮点（Highlights）

- 首次公开发布：`load_random_data()` 与 `load_history_data()`，
  覆盖官方福彩/体彩接口。
