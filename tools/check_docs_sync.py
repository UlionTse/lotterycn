# coding=utf-8
"""Docs 双语同步守门（无第三方依赖，CI 与本地均可独立运行）。

规则：
1. 配对：docs 下每个 x.en.md 必须有对应的 x.zh.md，反之亦然。
2. 英文页禁中文：*.en.md 页面不得出现 CJK 字符；
   仅豁免 games.en.md 表格行（彩种名为官方专有名词，保留中文原名）。
3. 定位词一致：英文语料必须含 "enjoyable"、中文语料必须含 "有趣"
   （README 与文档站首页的标语位）。缺失即视为中英漂移。
4. 域名纪律：全仓 *.md 不得出现内部数据 API 域名（webapi.sporttery.cn）；
   代码层 *.py 不受限（端点常量是功能实现）。

用法：python tools/check_docs_sync.py    退出码 0=通过，1=存在违规。
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")

# 规则 2 豁免：文件名 -> 行谓词；谓词为真的行允许含 CJK
_CJK_LINE_ALLOWLIST = {
    "games.en.md": lambda line: line.lstrip().startswith("|"),
}

# 规则 3：(文件, 必须包含的定位词)
_TAGLINE_REQUIREMENTS = [
    (ROOT / "README.md", "enjoyable"),
    (ROOT / "README_zh.md", "有趣"),
    (DOCS / "index.en.md", "enjoyable"),
    (DOCS / "index.zh.md", "有趣"),
]

# 规则 4：*.md 中禁止出现的内部数据 API 域名（代码层不受限）
_BANNED_DOMAINS = ("webapi.sporttery.cn",)
_SKIP_PARTS = {".venv", ".git", "site", "_site_new", "build", "node_modules"}


def _base_key(path):
    """去掉 .en/.zh 语言后缀，返回页面在 docs 下的相对键。"""
    name = path.name
    for suffix in (".en.md", ".zh.md"):
        if name.endswith(suffix):
            return str(path.parent.relative_to(DOCS) / name[: -len(suffix)])
    return None


def check_pairs(problems):
    en_keys = {_base_key(p) for p in DOCS.rglob("*.en.md")}
    zh_keys = {_base_key(p) for p in DOCS.rglob("*.zh.md")}
    en_keys.discard(None)
    zh_keys.discard(None)
    for key in sorted(en_keys - zh_keys):
        problems.append(f"[pairs] 缺中文页：{key}.zh.md")
    for key in sorted(zh_keys - en_keys):
        problems.append(f"[pairs] 缺英文页：{key}.en.md")


def check_cjk_in_english(problems):
    for page in sorted(DOCS.rglob("*.en.md")):
        allow = _CJK_LINE_ALLOWLIST.get(page.name)
        text = page.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not _CJK.search(line):
                continue
            if allow is not None and allow(line):
                continue
            snippet = line.strip()
            if len(snippet) > 60:
                snippet = snippet[:60] + "..."
            problems.append(f"[cjk] {page.relative_to(ROOT)}:{lineno} 英文页含中文：{snippet}")


def check_taglines(problems):
    for path, word in _TAGLINE_REQUIREMENTS:
        rel = path.relative_to(ROOT)
        if not path.exists():
            problems.append(f"[tagline] 文件不存在：{rel}")
        elif word not in path.read_text(encoding="utf-8"):
            problems.append(f"[tagline] {rel} 缺少定位词 {word!r}")


def check_banned_domains(problems):
    for page in sorted(ROOT.rglob("*.md")):
        if _SKIP_PARTS & set(page.parts):
            continue
        text = page.read_text(encoding="utf-8")
        for domain in _BANNED_DOMAINS:
            if domain in text:
                problems.append(f"[domain] {page.relative_to(ROOT)} 暴露内部数据 API 域名：{domain}")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    problems = []
    check_pairs(problems)
    check_cjk_in_english(problems)
    check_taglines(problems)
    check_banned_domains(problems)
    if problems:
        print(f"docs 双语同步检查未通过，共 {len(problems)} 处：")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("docs 双语同步检查通过：en/zh 配对完整，英文页无中文，定位词对齐。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
