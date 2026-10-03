# cache — Local cache

CSV cache with incremental refresh: full fetch on first run, then only draws newer than the latest cached date.

::: lotterycn.cache
    options:
      members:
        - DEFAULT_CACHE_DIR
        - get_cache_path
        - load_cached_history_data
