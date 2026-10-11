# coding=utf-8
"""从双语 CHANGELOG 抽取指定版本段落，生成 GitHub Release notes（英文段在上、中文段在下）。

用法：python tools/extract_changelog.py 1.0.1 [--out release_notes.md]
无 --out 时打印到 stdout；版本段落缺失时以非零码退出（CI 与本地均用于快速失败）。
"""

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def extract_section(text: str, version: str, source: str) -> str:
    """返回 `## [version]` 段落（含标题行）到下一个 `## [` 之前的内容。"""
    heading = re.compile(rf"^## \[{re.escape(version)}\]\s*.*$", re.MULTILINE)
    match = heading.search(text)
    if match is None:
        raise SystemExit(f"{source}: 未找到版本段落 '## [{version}]'，请先在 CHANGELOG 中补齐")
    tail = text[match.end() :]
    nxt = re.search(r"^## \[", tail, re.MULTILINE)
    end = match.end() + (nxt.start() if nxt else len(tail))
    return text[match.start() : end].rstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate bilingual GitHub Release notes from CHANGELOG files.")
    parser.add_argument("version", help="版本号，如 1.0.1（不含 v 前缀）")
    parser.add_argument("--out", default=None, help="输出文件路径；缺省打印到 stdout")
    args = parser.parse_args()

    english = extract_section((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), args.version, "CHANGELOG.md")
    chinese = extract_section((ROOT / "CHANGELOG_zh.md").read_text(encoding="utf-8"), args.version, "CHANGELOG_zh.md")
    notes = f"{english}\n\n---\n\n{chinese}\n"

    if args.out:
        pathlib.Path(args.out).write_text(notes, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
