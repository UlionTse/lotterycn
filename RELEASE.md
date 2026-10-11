# 发布流程（Release Guide）

> 维护者指南：本项目的发布已从「本地 build → twine upload」（≤0.0.4）、
> 「tag 推送即上传」（1.0.0）迁移为 **Release 驱动的可信发布**（1.0.1 起）：
> tag 推送只自动生成双语草稿 Release，**点击 Publish Release 才触发 PyPI 上传**。
> 本文描述完整流程与失败补救。

## 0. 流程一览与历史沿革

| | 旧流程（≤0.0.4） | tag 驱动（1.0.0） | **Release 驱动（1.0.1 起，本流程）** |
|---|---|---|---|
| 构建 | 本地 `python -m build` | GitHub Actions | GitHub Actions |
| 上传 | `twine upload ./dist/*`（需 token） | `pypa/gh-action-pypi-publish`（**OIDC Trusted Publisher**，无 token） | 同左 |
| 触发 | 手动执行即发布 | **push `v*` tag 即上传 PyPI** | **Publish Release 才上传 PyPI**；tag 推送仅生成双语草稿 |
| Release notes | 手写 | 手动在网页粘贴 | 自动从双语 CHANGELOG 抽取预填 |
| 版本守卫 | 无 | 无 | tag 与 `__version__` 在两个 workflow 中自动校验 |

两个 workflow 的分工：

- **`prepare-release.yml`**（tag 推送触发）：校验 tag 与 `__version__` 一致 →
  `tools/extract_changelog.py` 从 `CHANGELOG.md` / `CHANGELOG_zh.md` 抽取该版本段落 →
  自动创建 **Draft Release**（英文段在上、中文段在下，分隔线隔开）。
- **`release.yml`**（Release 发布触发）：再次校验版本 → 干净环境构建 → Trusted Publisher 上传 PyPI。

## 1. 一次性配置（仅首次发布前）

### 1.1 PyPI Trusted Publisher（一次性）

`lotterycn` 在 PyPI 上**已存在**（0.0.4 与 1.0.0 均已上传），在已有项目的管理页维护：

1. 登录 [pypi.org](https://pypi.org) → 进入项目 [lotterycn](https://pypi.org/project/lotterycn/) →
   **Manage → Publishing → Trusted Publisher**
2. 四要素必须与 `release.yml` 严格一致：

| 字段 | 值 |
|---|---|
| Owner | `UlionTse` |
| Repository | `lotterycn` |
| Workflow name | `release.yml` |
| Environment | `pypi` |

3. 说明：触发方式从 tag 推送改为 Release 发布**不影响** Trusted Publisher 登记
   （TP 只关心上面四要素）；1.0.0 前的配置原样有效。

### 1.2 GitHub 仓库设置

- **Environments**：名为 `pypi` 的环境（与 `release.yml` 的 `environment: pypi` 和
  TP 登记逐字符一致）。首次 Release workflow 运行时会自动创建，无需手动建。
  注意 **Deployment protection rules**：若启用了 Required reviewers（新建 environment
  的常见配置），每次发布 run 会停在 "Review deployments" 等待人工批准（操作见 §3
  步骤 5）；不想要此手工环节，在 Settings → Environments → pypi 里删除该保护规则。
  Deployment branch and tag policies 限定 `v*` 是另一项可选加固，与审批互不影响。
- **Pages**：Source 选 **gh-pages 分支 + / (root)**（`docs.yml` 每次 push main 自动
  `mkdocs gh-deploy` 重建，保持 **Deploy from a branch** 模式，不要选 "GitHub Actions"）。
- **Actions 权限**：保持默认受限即可；`release.yml` 已显式声明
  `permissions: id-token: write`，`prepare-release.yml` 已声明 `contents: write`（创建草稿所需）。

### 1.3 本机（可选）

本地不再需要 build/twine 参与发布。如需本地验证构建产物：
`pip install -e .[pypi] && python -m build`——产物仅作检查，**不上传**。

## 2. 发布前检查清单（每次发布）

- [ ] `lotterycn/__init__.py` 的 `__version__` 已改为目标版本（动态版本从此读取，
      **必须与 tag 严格一致**，两个 workflow 均会校验）
- [ ] `CHANGELOG.md` / `CHANGELOG_zh.md` 已有对应版本的 `## [x.y.z] - 日期` 段落
      （草稿 notes 从这里抽取；**缺段落时 prepare-release 会直接失败**）
- [ ] 本地全绿：

  ```shell
  ruff check lotterycn tests tools
  ruff format --check lotterycn tests tools hooks.py
  mypy
  pytest -m "not network" --cov=lotterycn
  mkdocs build --strict
  ```

- [ ] （可选）`python -m build` 后检查 `dist/` 文件名版本正确（本地产物仅验证，不上传）

## 3. 标准发布步骤（以 v1.0.1 为例）

```shell
# 1) 准备版本
#    - lotterycn/__init__.py：__version__ = "1.0.1"
#    - CHANGELOG.md / CHANGELOG_zh.md：新增 "## [1.0.1] - YYYY-MM-DD" 双语段落
git add .
git commit -m "release: v1.0.1"

# 2) 推 main，等待 CI 全绿（测试矩阵 + 文档部署）
git push origin main
#    → Actions 页确认 CI ✓ 与 Docs ✓（文档站此时已更新）

# 3) 打 tag 并推送 —— 触发 prepare-release.yml
git tag -a v1.0.1 -m "lotterycn 1.0.1"
git push origin v1.0.1
#    → Actions 页出现 "Prepare Release"：Guard → Extract notes → Create draft release
#    → Releases 页出现草稿 "lotterycn 1.0.1"，notes 为英文段 + 中文段

# 4) 发布草稿（在 Releases 页面操作；草稿仅维护者登录后可见）：
#    ① 仓库页 → Releases → 点开 Draft 状态的 "lotterycn 1.0.1"
#    ② 点右上角铅笔图标 ✏️（Edit release）进入编辑表单
#    ③ 确认发布信息：Tag = v1.0.1、Title = lotterycn 1.0.1、notes 为
#       英文段 + 分隔线 + 中文段（需要微调在此编辑）
#    ④ 拉到表单底部 → 点绿色 "Publish release" 按钮 —— 触发 Release workflow
#
# 5) 人工批准环境部署（若 pypi 环境启用了 Required reviewers）
#    → Actions 页 Release run 顶部出现 "Review deployments" 按钮
#    → 勾选 pypi 环境 → 点击 "Approve and deploy"
#    → job 开始执行：Guard → Build → Publish to PyPI
#    （未启用 Required reviewers 时无此步，job 自动开始）
```

补充说明：

- 第 4 步也可用命令行发布：`gh release edit v1.0.1 --draft=false`（发布前先在网页
  或 `gh release view v1.0.1` 校对 notes）。
- **手动替代路径**（不依赖 prepare-release.yml）：

  ```shell
  python tools/extract_changelog.py 1.0.1 --out release_notes.md
  gh release create v1.0.1 --title "lotterycn 1.0.1" --notes-file release_notes.md --draft
  # 网页校对后 Publish（或 gh release edit v1.0.1 --draft=false）
  ```

- notes 需要微调时直接编辑草稿再 Publish；也可 `python tools/extract_changelog.py 1.0.1`
  打印到终端核对。

## 4. 发布后验证

1. **Actions**：Prepare Release 与 Release 两个 workflow 全绿。
2. **GitHub Release**：Releases 页出现非草稿的 v1.0.1，notes 为英文段 + 分隔线 + 中文段。
3. **PyPI**：`https://pypi.org/project/lotterycn/` 出现 1.0.1；干净 venv 验证：

   ```shell
   pip install lotterycn
   python -c "import lotterycn; print(lotterycn.__version__)"
   ```

4. **文档站**：`https://uliontse.github.io/lotterycn/` 已更新（main 推送时由 docs.yml 部署）。
5. **README 徽章**：PyPI version / license / python / downloads 自动点亮。
   **conda-forge 已收录 lotterycn**：上 PyPI 后，regro 自动化机器人通常会对 feedstock
   自动发起版本更新 PR，维护者审核合并即可点亮（无需 staged-recipes 新建流程）。
6. **site/ 双轨说明**：仓库内提交的 `site/` 只是静态副本（供本地/离线预览）；
   线上 Pages 由 docs.yml 重建，两者独立、互不依赖。

## 5. 失败与补救

| 症状 | 原因 | 处置 |
|---|---|---|
| Prepare Release 的 Guard 步骤失败 | tag 与 `__version__` 不一致 | 修 `__version__` 后删 tag 重打：`git tag -d vX && git push origin :refs/tags/X`（此时尚未上传 PyPI，安全） |
| Extract notes 步骤失败 | CHANGELOG 无对应版本段落 | 补双语段落 → 删 tag 重打 |
| 草稿 notes 有误 | 抽取内容需微调 | 直接编辑草稿再 Publish；或删掉草稿重跑 workflow |
| Publish 前想撤回 | 草稿误建 | Delete release（草稿不触发任何上传）→ 修正后重走 §3 步骤 3-4 |
| run 停在 "Review deployments"，无任何步骤执行 | pypi 环境启用了 Required reviewers | run 页点 **Review deployments** → 勾选 `pypi` → **Approve and deploy**；不想要手工批准：Settings → Environments → pypi 删除该保护规则 |
| Publish 步骤 401/403 | Trusted Publisher 未登记或四要素不符 | 核对 §1.1 四要素 → **Re-run failed jobs** |
| 同版本号上传冲突 | PyPI 版本不可覆盖、不可删除重传 | 内容有问题：**yank** 该版本 + 修复后发新版本，绝不重传同号 |
| tag 打错且草稿已建 | — | 删草稿 + 删 tag 重打；**若已上传 PyPI 则只能往前发新版本** |
| conda 用户装不到 | conda-forge 未同步 | 等 regro bot PR 或手动对 feedstock 发 PR，与本流程解耦 |

## 6. 后续小版本（1.0.2 起同构）

1. 改 `__version__` → 2. CHANGELOG 双语增段 → 3. 本地全绿 → 4. commit / push main、CI 绿 →
5. `git tag -a vX.Y.Z` 并推送（生成双语草稿）→ 6. Publish Release →（如启用 Required reviewers）
   在 run 页 Approve and deploy → 7. 按 §4 验证。

## 7. 可选增强（暂未实现）

- PyPI 项目页链接校验（`[project.urls]` 的 Documentation 指向文档站）；
- release.yml 构建后校验 wheel 文件名版本（当前 Guard 已校验 `__init__.py`，此为补充）。

已实现的增强（原 TODO）：tag 与 `__version__` 校验、GitHub Release 自动创建并附双语 CHANGELOG 段落。
