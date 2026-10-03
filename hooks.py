# coding=utf-8
"""MkDocs hook: 产物 HTML 轻量规整 + 多语言链接相对化。

- 折叠 3+ 连续空行、去行尾空格；<pre> 代码块内容原样保护；
- 把 site_url 派生的绝对路径链接（如 /lotterycn/zh/…）按页面深度重写为相对
  路径，使语言切换器在本地 IDE 预览、离线打开、GitHub Pages 项目路径下
  全部可用。
"""
import pathlib
import re
from urllib.parse import urlparse

_BLANK_RUNS = re.compile(r"\n{3,}")
_PRE_BLOCKS = re.compile(r"(<pre\b.*?</pre>)", re.DOTALL | re.IGNORECASE)


def on_post_build(config, **kwargs):
    site_dir = pathlib.Path(config["site_dir"])
    site_url = (config.get("site_url") or "").rstrip("/")
    path_prefix = urlparse(site_url).path.rstrip("/") if site_url else ""

    for f in site_dir.rglob("*.html"):
        text = f.read_text(encoding="utf-8")

        # 1) 绝对路径前缀 → 按页面深度相对化
        if path_prefix and f'href="{path_prefix}/' in text:
            depth = len(f.parent.relative_to(site_dir).parts)
            prefix = "./" if depth == 0 else "../" * depth
            text = text.replace(f'href="{path_prefix}/', f'href="{prefix}')

        # 2) 格式规整（<pre> 保护）
        parts = _PRE_BLOCKS.split(text)
        for i, part in enumerate(parts):
            if i % 2 == 0:
                part = "\n".join(line.rstrip() for line in part.split("\n"))
                part = _BLANK_RUNS.sub("\n\n", part).lstrip("\n")
                parts[i] = part
        normalized = "".join(parts)
        if normalized != text:
            f.write_text(normalized, encoding="utf-8", newline="\n")
