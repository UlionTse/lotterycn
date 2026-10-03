# 发布流程（Release Guide）

> 维护者指南：本项目的发布已从「本地 build → twine upload → git push」三步，
> 迁移为 **tag 驱动的可信发布**。本文描述完整流程与失败补救。

## 0. 与旧流程的差别

| | 旧流程 | 本流程 |
|---|---|---|
| 构建 | 本地 `python -m build` | GitHub Actions 干净环境构建（`release.yml`） |
| 上传 | `twine upload ./dist/*`（需 token） | `pypa/gh-action-pypi-publish`（**OIDC Trusted Publisher**，无 token） |
| 触发 | 手动执行即发布 | **仅 `v*` tag 推送触发**；push main 只跑测试与文档部署 |
| 可复现性 | 依赖本地环境 | CI 产物可复现、来源可信（Sigstore 签名自动附带） |

## 1. 一次性配置（仅首次发布前）

### 1.1 PyPI Trusted Publisher（一次性）

`lotterycn` 在 PyPI 上**已存在**（最新 0.0.4，2022-11 经 twine/4.0.1 上传），因此**不走
pending publisher 预登记**，直接在已有项目的管理页添加：

1. 登录 [pypi.org](https://pypi.org) → 进入项目 [lotterycn](https://pypi.org/project/lotterycn/) →
   **Manage → Publishing → Add Trusted Publisher**
2. 四要素必须与 `release.yml` 严格一致：

| 字段 | 值 |
|---|---|
| Owner | `UlionTse` |
| Repository | `lotterycn` |
| Workflow name | `release.yml` |
| Environment | `pypi` |

3. 与旧 twine 流程的关系：
   - 0.0.x 的历史版本原样保留，与 1.0.0 无版本号冲突（1.0.0 > 0.0.4）；
   - **旧 API token 无需迁移**——OIDC 全程不用 token，`release.yml` 中也无任何 token 引用；
     旧 token 若已不再用于其他项目，可在账户设置中删除（可选的卫生操作）。

### 1.2 GitHub 仓库设置

- **Environments**：目标是在此创建名为 `pypi` 的环境（与 release.yml 的 `environment: pypi`
  和 PyPI Trusted Publisher 登记逐字符一致）。按页面状态二选一：
  - 菜单存在但列表为空（"There are no environments..."）→ 点 **New environment** →
    Name 填 `pypi` → Configure environment。
  - 侧栏没有 Environments 菜单 → 先到 Settings → Actions 确认 GitHub Actions 已启用；
    或走懒路径：直接跳过——Release workflow 首次运行时会自动创建 `pypi` 环境，发布不会
    因此失败，菜单会随之出现。
  - 创建后的可选加固：Deployment branch and tag policies 限定 `v*`；或加 required reviewers。
- **Pages**（分两步，别提前配）：**现在什么都不用选**——下拉里只有 `main`（唯一已推送的分支），
  选它会指向错误内容（main 根目录没有构建产物）。正确顺序：
  ① 按 §3 推送 main 后，`docs.yml` 会执行 `mkdocs gh-deploy --force`，自动创建 `gh-pages` 分支；
  ② 回到本页，Source 下拉里此时才会出现 `gh-pages` → 选 **gh-pages 分支 + / (root)** → Save。
  注意 Source 保持 **Deploy from a branch** 模式（docs.yml 用的是 `mkdocs gh-deploy`，不是官方
  Pages actions，不要选 "GitHub Actions"）。此后每次 push main 自动重新部署，无需再动。
- **Actions 权限**：保持默认受限即可，`release.yml` 已显式声明 `permissions: id-token: write`。

### 1.3 本机（可选）

本地不再需要 build/twine 参与发布。如需本地验证构建产物：
`pip install -e .[pypi] && python -m build`——产物仅作检查，**不上传**。

## 2. 发布前检查清单（每次发布）

- [ ] `lotterycn/__init__.py` 的 `__version__` 已改为目标版本（动态版本从此读取，**必须与 tag 严格一致**）
- [ ] `CHANGELOG.md` / `CHANGELOG_zh.md` 对应版本段落与日期已就绪
- [ ] 本地全绿：

  ```shell
  ruff check lotterycn tests tools/check_docs_sync.py
  ruff format --check lotterycn tests
  mypy
  pytest -m "not network" --cov=lotterycn
  mkdocs build --strict
  ```

- [ ] （可选）`python -m build` 后检查 `dist/` 文件名版本正确（本地产物仅验证，不上传）

## 3. 标准发布步骤

```shell
# 1) 提交全部改动
git add .
git status          # 确认 tools/logo/ 与 _tmp_* 不在列表中（已 gitignore）
git commit -m "release: v1.0.0"

# 2) 推 main，等待 CI 全绿（test 矩阵 + Docs 部署）
git push origin main
#    → Actions 页确认 CI ✓ 与 Docs ✓（文档站此时已更新）

# 3) 打 tag 并推送 —— 此步触发 PyPI 发布
git tag -a v1.0.0 -m "lotterycn 1.0.0"
git push origin v1.0.0
#    → Actions 页出现 Release workflow：Build → Publish to PyPI（Trusted Publisher，无 token）
```

## 4. 发布后验证

1. **Actions**：Release job 全绿（Build → Publish to PyPI）。
2. **PyPI**：`https://pypi.org/project/lotterycn/` 出现 1.0.0；干净 venv 验证：

   ```shell
   pip install lotterycn
   python -c "import lotterycn; print(lotterycn.__version__)"
   ```

3. **文档站**：`https://uliontse.github.io/lotterycn/` 已更新（main 推送时由 docs.yml 部署）。
4. **GitHub Release**：Releases → Draft a new release → 选择 tag `v1.0.0` → 把 CHANGELOG 的
   1.0.0 段落粘贴为 notes（或 `gh release create v1.0.0 --title "1.0.0" --notes-file ...`）。
5. **README 徽章**：PyPI version / license / python / downloads 自动点亮。
   **conda-forge 已收录 lotterycn（0.0.4）**：1.0.0 上 PyPI 后，regro 自动化机器人通常会对
   feedstock 自动发起版本更新 PR，维护者审核合并即可点亮（无需 staged-recipes 新建流程）。
6. **site/ 双轨说明**：仓库内提交的 `site/` 只是静态副本（供本地/离线预览）；
   线上 Pages 由 docs.yml 重建，两者独立、互不依赖。

## 5. 失败与补救

| 症状 | 原因 | 处置 |
|---|---|---|
| Publish 步骤 401/403 | Trusted Publisher 未登记或四要素不符 | 核对 1.1 的五项 → **Re-run failed jobs**（tag 不用动） |
| 同版本号上传冲突 | PyPI 版本不可覆盖、不可删除重传 | 内容有问题：**yank** 该版本 + 修复后发 1.0.1，绝不重传同号 |
| tag 打错 / 忘改 `__version__` | Release 尚未跑或已失败 | 删 tag 重打：`git tag -d v1.0.0 && git push origin :refs/tags/v1.0.0`；**若已上传 PyPI 则只能往前发新版本** |
| conda 用户装不到 | conda-forge 未收录 | 走 conda-forge/staged-recipes 独立 PR，与本流程解耦 |

## 6. 后续小版本（1.0.1 起同构）

1. 改 `__version__` → 2. CHANGELOG 双语增段 → 3. 本地全绿 → 4. commit / push main、CI 绿 →
   5. `git tag -a v1.0.1` 并推送 → 6. 按 §4 验证。

## 7. 可选增强（暂未实现）

- release.yml 构建后校验 wheel 版本号与 tag 一致（防 tag 与 `__version__` 漂移）；
- PyPI 项目页链接校验（`[project.urls]` 的 Documentation 指向文档站）；
- GitHub Release 由 workflow 自动创建并附 CHANGELOG 段落。
