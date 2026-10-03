# cache — 本地缓存

CSV 缓存与增量更新：首次全量拉取落盘，之后仅拉取最后开奖日期之后的数据。

::: lotterycn.cache
    options:
      members:
        - DEFAULT_CACHE_DIR
        - get_cache_path
        - load_cached_history_data
